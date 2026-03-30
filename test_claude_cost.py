import requests
import json
import time
import uuid
import os

SPLUNK_HEC_URL = "https://localhost:8088/services/collector"
SPLUNK_HEC_TOKEN = os.environ.get("SPLUNK_HEC_TOKEN")

def send_test_event(model_name, provider="anthropic"):
    trace_id = str(uuid.uuid4()).replace('-', '')
    span_id = str(uuid.uuid4()).replace('-', '')[:16]
    
    metrics = {
        "model_name": model_name,
        "model_provider": provider,
        "span_type": "LLM",
        "input_tokens": 1000,
        "output_tokens": 500,
        "duration_ms": 1500,
        "trace_id": trace_id,
        "span_id": span_id,
        "timestamp": time.time(),
        "gen_ai.usage.input_tokens": 1000,
        "gen_ai.usage.output_tokens": 500,
        "gen_ai.request.model": model_name,
        "gen_ai.system": provider
    }
    
    payload = {
        "index": "genai_traces",
        "event": metrics,
        "sourcetype": "genai:trace"
    }
    
    headers = {"Authorization": f"Splunk {SPLUNK_HEC_TOKEN}"}
    
    try:
        response = requests.post(SPLUNK_HEC_URL, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        print(f"Sent test event for {model_name}: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test existing model in lookup (claude-3.5-sonnet)
    print("Testing 'claude-3.5-sonnet' (current lookup value)...")
    send_test_event("claude-3.5-sonnet")
    
    # Test model name used in mcp_server.py (claude-3-5-sonnet)
    print("\nTesting 'claude-3-5-sonnet' (mcp_server.py value)...")
    send_test_event("claude-3-5-sonnet")
