import requests
import json
import time
import random
import uuid
import os
import datetime

# Configuration
SPLUNK_URL = os.getenv('SPLUNK_HEC_URL', 'https://localhost:8088/services/collector')
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', 'bb3b876d-a885-4820-8675-3fb520ac221d')
LAB_USER_ID = os.getenv('LAB_USER_ID', 'shared')

models = ["gemma3:1b", "qwen2.5:7b", "qwen3:4b"]

def send_mock_event(timestamp):
    model = random.choice(models)
    input_tokens = random.randint(100, 500)
    output_tokens = random.randint(50, 300)
    duration_ms = random.uniform(2000, 8000)
    
    metrics = {
        "model_name": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "user": LAB_USER_ID,
        "timestamp": timestamp.isoformat()
    }
    
    payload = {
        "index": "genai_traces",
        "event": metrics,
        "sourcetype": "genai:trace",
        "time": timestamp.timestamp()
    }
    
    try:
        # Disable SSL verification for local dev/lab
        requests.post(SPLUNK_URL, headers={"Authorization": f"Splunk {SPLUNK_TOKEN}"}, json=payload, verify=False, timeout=5)
    except Exception as e:
        pass

if __name__ == "__main__":
    count = 181
    print(f"Repopulating {count} events for user {LAB_USER_ID}...")
    base_time = datetime.datetime.now() - datetime.timedelta(hours=1)
    
    for i in range(count):
        offset = random.randint(0, 3600)
        timestamp = base_time + datetime.timedelta(seconds=offset)
        send_mock_event(timestamp)
        if i % 50 == 0:
            print(f"Sent {i} events...")
            
    print("Repopulation complete.")
