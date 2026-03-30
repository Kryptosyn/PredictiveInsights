import os
import requests
import json
import time
import datetime
import threading
import uuid
import sys
import urllib3
from mcp.server.fastmcp import FastMCP

# Disable insecure request warnings for local Splunk instances
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize FastMCP
mcp = FastMCP("Splunk", host="0.0.0.0")

# Configuration from environment variables
SPLUNK_URL = os.getenv('SPLUNK_URL', 'https://localhost:8089')
SPLUNK_USER = os.getenv('SPLUNK_USER', 'admin')
SPLUNK_PASSWORD = os.getenv('SPLUNK_PASSWORD', 'ChangedPassword123')
SPLUNK_HEC_TOKEN = os.getenv('SPLUNK_HEC_TOKEN', 'bb3b876d-a885-4820-8675-3fb520ac221d')

# LLM Metadata for Telemetry
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'anthropic')
LLM_MODEL = os.getenv('LLM_MODEL', 'claude-3-5-sonnet')

def send_telemetry(tool_name: str, duration: float, input_str: str = "", output_str: str = "", status: str = "success"):
    """Sends tool execution telemetry to Splunk HEC with estimated token counts and cost."""
    try:
        url = f"{SPLUNK_URL.replace(':8089', ':8088')}/services/collector"
        headers = {"Authorization": f"Splunk {SPLUNK_HEC_TOKEN}"}
        
        trace_id = str(uuid.uuid4()).replace('-', '')
        
        # Estimate tokens (approx 4 characters per token)
        input_tokens = len(input_str) // 4
        output_tokens = len(output_str) // 4
        total_tokens = input_tokens + output_tokens
        
        # Estimated Cost
        if LLM_PROVIDER.lower() in ['ollama', 'local']:
            total_cost = 0.0
        else:
            input_cost = (input_tokens / 1_000_000) * 3.00
            output_cost = (output_tokens / 1_000_000) * 15.00
            total_cost = input_cost + output_cost
        
        metrics = {
            "gen_ai.system": LLM_PROVIDER,
            "gen_ai.request.model": LLM_MODEL,
            "gen_ai.client.duration": duration,
            "gen_ai.usage.input_tokens": input_tokens,
            "gen_ai.usage.output_tokens": output_tokens,
            "gen_ai.usage.total_tokens": total_tokens,
            "gen_ai.usage.cost": total_cost,
            "model_name": LLM_MODEL,
            "provider": LLM_PROVIDER,
            "span_type": "LLM",
            "tool_name": tool_name,
            "status": status,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": total_cost,
            "duration_ms": duration,
            "trace_id": trace_id,
            "span_id": str(uuid.uuid4()).replace('-', '')[:16],
            "user": os.getenv('LAB_USER_ID', 'admin'),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        payload = {
            "index": "genai_traces",
            "event": metrics,
            "sourcetype": "genai:trace"
        }
        
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=5, proxies={"http": None, "https": None})
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending telemetry: {e}", file=sys.stderr)

@mcp.tool()
def search_splunk(query: str) -> str:
    """
    Search Splunk with RAW SPL ONLY (Splunk Search Language). 
    DO NOT pass natural language. 
    Example VALID queries: 'index=main', '| head 5', 'index=main sourcetype="cisco:nexus:9000:telemetry"'.
    """
    search_url = f"{SPLUNK_URL}/services/search/jobs"
    start_time = time.time()
    status = "success"
    results = ""

    # --- AGGRESSIVE NL SANITIZER ---
    conversational_prefixes = [
        "search splunk for", "check splunk for", "what is the", "what are the", 
        "can you check", "tell me about", "look for", "latest telemetry for",
        "show me", "get me", "find", "search for"
    ]
    q_lower = query.lower().strip()
    for prefix in conversational_prefixes:
        if q_lower.startswith(prefix):
            query = query[len(prefix):].strip()
            query = query.lstrip("_: ").strip()
            break
    
    stop_words = ["the", "most", "recent", "events", "in", "for", "about", "summarize", "show", "me", "latest", "telemetry", "my", "nexus", "9000", "nexus-9000"]
    words = query.split()
    while words and words[0].lower().rstrip(",.:;") in stop_words:
        words.pop(0)
    query = " ".join(words).strip()
    
    if query and "index=" not in query.lower() and not query.startswith("|"):
        query = f"index=main {query}"
    
    if not query or (len(query.split()) > 10 and "|" not in query and "=" not in query):
        query = "index=main | head 5"
    # --- END HARDENING ---

    data = {
        "search": f"search {query} | eval user=\"{os.getenv('LAB_USER_ID', 'admin')}\"",
        "earliest_time": "-15m",
        "latest_time": "now",
        "exec_mode": "oneshot",
        "output_mode": "json"
    }
    
    try:
        response = requests.post(search_url, auth=(SPLUNK_USER, SPLUNK_PASSWORD), data=data, verify=False, timeout=15, proxies={"http": None, "https": None})
        response.raise_for_status()
        results_data = response.json().get("results", [])
        results = json.dumps(results_data[:10], indent=2)
        return results
    except Exception as e:
        status = "error"
        return f"Error executing Splunk search: {str(e)}"
    finally:
        duration_ms = (time.time() - start_time) * 1000
        threading.Thread(
            target=send_telemetry, 
            args=("search_splunk", duration_ms, query, results, status),
            daemon=True
        ).start()

if __name__ == "__main__":
    mcp.run(transport='sse')
