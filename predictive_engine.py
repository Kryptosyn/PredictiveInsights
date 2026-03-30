import os
import requests
import json
import time
import datetime

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434/api/generate')
SPLUNK_URL = os.getenv('SPLUNK_URL', 'http://127.0.0.1:8089/services/search/jobs')
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', 'bb3b876d-a885-4820-8675-3fb520ac221d')

def get_recent_telemetry():
    """Fetches recent telemetry from Splunk."""
    # This is a placeholder for actual Splunk API integration
    # In a real lab, you would run a search job and fetch results
    print("Fetching recent telemetry from Splunk...")
    return [
        {"device": "nexus-9000-01", "cpu_usage": 75, "interface_errors": 2, "timestamp": "2026-02-12T11:40:00"},
        {"device": "nexus-9000-01", "cpu_usage": 82, "interface_errors": 5, "timestamp": "2026-02-12T11:45:00"},
    ]

def send_token_metrics(metrics):
    """Sends GenAI metrics to Splunk HEC using OTel and app-specific conventions."""
    url = os.getenv('SPLUNK_HEC_URL', 'https://127.0.0.1:8088/services/collector')
    headers = {"Authorization": f"Splunk {SPLUNK_TOKEN}"}
    payload = {
        "index": "genai_traces",
        "event": metrics,
        "sourcetype": "genai:trace"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
        response.raise_for_status()
        print("GenAI Observability metrics sent to Splunk (index: genai_traces, sourcetype: genai:trace).")
    except Exception as e:
        print(f"Error sending metrics to Splunk: {e}")

def generate_forecast(telemetry_data):
    """Sends telemetry data to Ollama for predictive failure analysis."""
    # ... (prompt construction)
    prompt = f"""
    Analyze the following network telemetry data for a Cisco Nexus 9000 switch:
    {json.dumps(telemetry_data, indent=2)}

    Based on the trends (CPU usage increasing, errors rising), provide a predictive failure forecast.
    Identify potential root causes and recommend preventive actions.
    Format the output as 'Predictive Insight Report'.
    """

    print("Generating forecast using Ollama...")
    payload = {
        "model": "gemma3:1b",
        "prompt": prompt,
        "stream": False
    }

    import uuid
    trace_id = str(uuid.uuid4()).replace('-', '')

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180) # Increased timeout
        response.raise_for_status()
        resp_json = response.json()
        
        # GenAI Observability: Extract metrics using dual conventions (OTel + App Specific)
        metrics = {
            # OTel Standard Fields
            "gen_ai.request.model": resp_json.get("model"),
            "gen_ai.usage.input_tokens": resp_json.get("prompt_eval_count"),
            "gen_ai.usage.output_tokens": resp_json.get("eval_count"),
            "gen_ai.usage.total_tokens": resp_json.get("prompt_eval_count", 0) + resp_json.get("eval_count", 0),
            "gen_ai.client.duration": resp_json.get("total_duration", 0) / 1_000_000_000, # seconds
            "gen_ai.system": "ollama",
            
            # App-Specific Fields (from props.conf/transforms.conf)
            "model_name": resp_json.get("model"),
            "model_provider": "ollama",
            "input_tokens": resp_json.get("prompt_eval_count"),
            "output_tokens": resp_json.get("eval_count"),
            "duration_ms": resp_json.get("total_duration", 0) / 1_000_000, # ms
            "span_type": "LLM",
            "trace_id": trace_id,
            "span_id": str(uuid.uuid4()).replace('-', '')[:16],
            
            "user": os.getenv('LAB_USER_ID', 'default_user'),
            "timestamp": datetime.datetime.now().isoformat()
        }
        send_token_metrics(metrics)
        
        return resp_json.get('response', 'No response from Ollama')
    except Exception as e:
        return f"Error communicating with Ollama: {e}"

if __name__ == "__main__":
    data = get_recent_telemetry()
    forecast = generate_forecast(data)
    print("\n--- PREDICTIVE INSIGHT REPORT ---")
    print(forecast)
