import requests
import json
import time
import uuid
import datetime
import os

SPLUNK_HEC_URL = "https://localhost:8088/services/collector"
SPLUNK_HEC_TOKEN = "bb3b876d-a885-4820-8675-3fb520ac221d"

def send_test_event(model_name, provider):
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
        "timestamp": datetime.datetime.now().isoformat(),
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
        print(f"Sent test event for {model_name} ({provider}): {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test Llama3 (Ollama) - Newly added
    print("Testing 'llama3' (ollama)...")
    send_test_event("llama3", "ollama")
    
    # Test Claude naming fix
    print("\nTesting 'claude-3-5-sonnet' (mcp_server.py alias)...")
    send_test_event("claude-3-5-sonnet", "anthropic")
    
    # Test existing Claude model
    print("\nTesting 'claude-3.5-sonnet' (original lookup)...")
    send_test_event("claude-3.5-sonnet", "anthropic")
