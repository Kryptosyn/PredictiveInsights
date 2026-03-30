import os
import sys
import json
import uuid
import time
import datetime
import requests
import threading
from flask import Flask, request, Response, stream_with_context

import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Configuration
PROXY_HOST = "0.0.0.0"
PROXY_PORT = int(os.environ.get("PROXY_PORT", "11435"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
SPLUNK_URL = os.environ.get("SPLUNK_URL", "https://localhost:8088/services/collector")
SPLUNK_TOKEN = os.environ.get("SPLUNK_TOKEN")

# Setup Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(level=logging.INFO)
file_handler = RotatingFileHandler("logs/ollama_proxy.log", maxBytes=1000000, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
app.logger.addHandler(file_handler)
app.logger.info(f"Ollama Proxy started, pointing to {OLLAMA_URL}")

def send_to_splunk(event):
    try:
        headers = {"Authorization": f"Splunk {SPLUNK_TOKEN}"}
        payload = {
            "time": time.time(),
            "host": "ollama_proxy",
            "source": "ollama_proxy",
            "sourcetype": "genai:trace",
            "index": "genai_traces",
            "event": event
        }
        resp = requests.post(SPLUNK_URL, headers=headers, json=payload, verify=False, timeout=5)
        print(f"Splunk HEC result: {resp.status_code}")
    except Exception as e:
        print(f"Splunk error: {e}")

# Cost per 1M tokens (Simulation)
MODEL_PRICING = {
    "gemma3:1b": {"input": 0.10, "output": 0.10},
    "llama3.1:8b": {"input": 0.15, "output": 0.20},
    "qwen2.5:7b": {"input": 0.12, "output": 0.15},
    "phi3:mini": {"input": 0.08, "output": 0.08},
    "default": {"input": 0.10, "output": 0.10}
}
USER_ID = os.environ.get("LAB_USER_ID", "shared")

def calculate_cost(model, input_tokens, output_tokens):
    price = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    cost = (input_tokens / 1_000_000 * price["input"]) + (output_tokens / 1_000_000 * price["output"])
    return round(cost, 6)

def run_evaluation(model, prompt, response, trace_id):
    """Background task to evaluate LLM response for hallucinations."""
    try:
        # Use gemma3:1b as the evaluator (fast and already loaded)
        eval_payload = {
            "model": "gemma3:1b",
            "messages": [
                {"role": "system", "content": "You are a factual accuracy evaluator. Rate the following LLM response on a scale of 0-1 (1 being perfectly factual and relevant) based on the user's prompt. Output ONLY the number."},
                {"role": "user", "content": f"Prompt: {prompt}\nResponse: {response}"}
            ],
            "stream": False
        }
        resp = requests.post(OLLAMA_URL + "/api/chat", json=eval_payload, timeout=10)
        if resp.status_code == 200:
            eval_data = resp.json()
            eval_text = eval_data.get("message", {}).get("content", "0.8").strip()
            try:
                score = float(eval_text)
            except:
                score = 0.9 # Default if parsing fails
            
            event = {
                "trace_id": trace_id,
                "span_type": "EVALUATION",
                "model": model,
                "gen_ai.model.name": model,
                "hallucination_score": score,
                "evaluator_model": "gemma3:1b",
                "user": USER_ID,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
            send_to_splunk(event)
    except Exception as e:
        print(f"Evaluation error: {e}")

def process_telemetry(req_json, res_json, duration_ms, trace_id):
    """Parses and sends various telemetry spans."""
    model = req_json.get("model", "unknown")
    
    # 1. LLM Span
    prompt_tokens = res_json.get("prompt_eval_count", 0)
    completion_tokens = res_json.get("eval_count", 0)
    total_tokens = prompt_tokens + completion_tokens
    cost = calculate_cost(model, prompt_tokens, completion_tokens)
    
    llm_event = {
        "trace_id": trace_id,
        "span_type": "LLM",
        "model": model,
        "model_name": model,
        "gen_ai.model.name": model,
        "input_tokens": prompt_tokens, # Duplicated for legacy macro compatibility
        "output_tokens": completion_tokens,
        "gen_ai.usage.input_tokens": prompt_tokens,
        "gen_ai.usage.output_tokens": completion_tokens,
        "gen_ai.usage.total_tokens": total_tokens,
        "cost": cost,
        "estimated_cost": cost, # Duplicated for single-value dashboard panels
        "duration_ms": duration_ms,
        "gen_ai.system": "ollama",
        "provider": "ollama",
        "is_error": 0,
        "user": USER_ID,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    send_to_splunk(llm_event)

    # 2. RAG Span (Detection)
    prompt_text = ""
    if "messages" in req_json:
        prompt_text = req_json["messages"][-1].get("content", "")
    elif "prompt" in req_json:
        prompt_text = req_json["prompt"]

    response_text = res_json.get("message", {}).get("content", "") or res_json.get("response", "")

    if "context" in req_json or "[Source" in response_text or "[[Source" in response_text or len(prompt_text) > 800:
        rag_event = {
            "trace_id": trace_id,
            "span_type": "RETRIEVER",
            "model": model,
            "gen_ai.model.name": model,
            "vector_store": "chromadb",
            "embedding_model": "all-minilm",
            "documents_retrieved": 3,
            "relevance_score": 0.95,
            "duration_ms": int(duration_ms * 0.2),
            "user": USER_ID,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        send_to_splunk(rag_event)

    # 3. Evaluation Span (Async)
    threading.Thread(target=run_evaluation, args=(model, prompt_text, response_text, trace_id)).start()

@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    print(f"Proxying: {path}")
    url = f"{OLLAMA_URL}/{path}"
    
    req_body = request.get_data()
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=req_body,
        cookies=request.cookies,
        allow_redirects=False,
        stream=True
    )

    # Important: Remove Content-Length and Transfer-Encoding when proxying/modifying stream
    excluded_headers = ['Content-Length', 'Transfer-Encoding', 'Host', 'Connection']
    proxied_headers = [(name, value) for (name, value) in resp.headers.items() 
                      if name not in excluded_headers]

    if path in ["api/chat", "api/generate"]:
        try:
            req_json = json.loads(req_body)
            is_streaming = req_json.get("stream", True)
        except:
            req_json = {}
            is_streaming = True

        if not is_streaming:
            def handle_non_stream():
                content = resp.content
                duration_ms = int((time.time() - start_time) * 1000)
                try:
                    res_json = json.loads(content)
                    process_telemetry(req_json, res_json, duration_ms, trace_id)
                except:
                    pass
                return content
            return Response(handle_non_stream(), resp.status_code, proxied_headers)
        else:
            def generate():
                full_response = ""
                final_json = {}
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        try:
                            chunk_str = chunk.decode("utf-8")
                            for line in chunk_str.split('\n'):
                                if not line: continue
                                data = json.loads(line)
                                if "message" in data:
                                    full_response += data["message"].get("content", "")
                                elif "response" in data:
                                    full_response += data.get("response", "")
                                if "prompt_eval_count" in data:
                                    final_json = data
                        except:
                            pass
                        yield chunk
                
                duration_ms = int((time.time() - start_time) * 1000)
                if final_json:
                    final_json["full_response_text"] = full_response
                    process_telemetry(req_json, final_json, duration_ms, trace_id)

            return Response(stream_with_context(generate()), resp.status_code, proxied_headers)

    return Response(resp.iter_content(chunk_size=1024), resp.status_code, proxied_headers)

if __name__ == "__main__":
    app.run(host=PROXY_HOST, port=PROXY_PORT, threaded=True)
