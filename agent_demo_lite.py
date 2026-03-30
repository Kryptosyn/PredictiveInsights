import os
import time
import requests
import json
from genai_telemetry import setup_splunk_telemetry, trace_agent, trace_tool

# 1. Setup Telemetry
setup_splunk_telemetry(
    workflow_name="agent-maintenance-demo",
    splunk_hec_url="https://localhost:8088",
    splunk_hec_token="bb3b876d-a885-4820-8675-3fb520ac221d",
    splunk_index="genai_traces"
)

# 2. Define the Proxy / Ollama Endpoint
# We point to port 11435 where our telemetry proxy is listening
OLLAMA_PROXY = "http://localhost:11435/api/chat"

# 3. Define the Tools
@trace_tool(tool_name="check_disk_space")
def check_disk_space():
    """Checks the current disk space."""
    print("[Agent] Executing tool: check_disk_space")
    time.sleep(1) # Simulate tool duration
    return "DISK FULL: 98% usage. Warning: Log folder contains large files."

@trace_tool(tool_name="list_logs")
def list_logs():
    """Lists files in the log directory."""
    print("[Agent] Executing tool: list_logs")
    time.sleep(1)
    return ["system.log (400MB)", "temp_debug.log (200MB)", "critical_config.json (10KB)"]

@trace_tool(tool_name="delete_file")
def delete_file(filename):
    """Deletes a specific file."""
    print(f"[Agent] Executing tool: delete_file ({filename})")
    time.sleep(2)
    return f"Success: {filename} has been removed."

# 4. Agent Logic (Simple Loop)
@trace_agent(agent_name="junior_admin_lite", agent_type="python_loop")
def run_agent():
    print("### STARTING JUNIOR_ADMIN_LITE AGENT ###")
    
    # Step 1: Initial Thought
    print("[Agent] Thinking: I need to check the disk space first.")
    result = check_disk_space()
    print(f"[Agent] Tool Result: {result}")
    
    # Step 2: Second Thought
    print("[Agent] Thinking: I should see what's in the log folder.")
    files = list_logs()
    print(f"[Agent] Tool Result: {files}")
    
    # Step 3: Decision & Action
    file_to_delete = files[0].split()[0]
    print(f"[Agent] Thinking: I will delete {file_to_delete} to free up space.")
    delete_result = delete_file(file_to_delete)
    print(f"[Agent] Tool Result: {delete_result}")
    
    # Step 4: Final LLM Confirmation (via Proxy)
    print("[Agent] Sending final report status to LLM...")
    payload = {
        "model": "gemma3:1b",
        "messages": [
            {"role": "user", "content": f"The junior_admin agent just completed a task. It deleted {file_to_delete}. Result bit: {delete_result}. Summarize the status."}
        ],
        "stream": False
    }
    try:
        resp = requests.post(OLLAMA_PROXY, json=payload, timeout=30)
        report = resp.json()
        print(f"\n[Agent] LLM Final Report: {report.get('message', {}).get('content', '')}")
    except Exception as e:
        print(f"[Agent] LLM Call Error: {e}")

    print("### TASK COMPLETE ###")

if __name__ == "__main__":
    run_agent()
    time.sleep(2) # ensure telemetry sends
