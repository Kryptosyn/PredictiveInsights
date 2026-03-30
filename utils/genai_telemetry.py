import functools
import os
import time
import datetime
import uuid
import requests
import json

# Global config storage
_config = {
    "url": "https://localhost:8088",
    "token": "bb3b876d-a885-4820-8675-3fb520ac221d",
    "index": "genai_traces",
    "user": os.getenv("LAB_USER_ID", "shared"),
    "workflow": "default"
}

def setup_splunk_telemetry(**kwargs):
    """Sets up global telemetry context."""
    global _config
    _config["url"] = kwargs.get("splunk_hec_url", _config["url"])
    _config["token"] = kwargs.get("splunk_hec_token", _config["token"])
    _config["index"] = kwargs.get("splunk_index", _config["index"])
    _config["workflow"] = kwargs.get("workflow_name", _config["workflow"])
    print(f"[TELEMETRY] Configured for workflow: {_config['workflow']}")

def send_telemetry(span_type, details):
    """Sends a telemetry event to Splunk HEC."""
    url = f"{_config['url'].rstrip('/')}/services/collector"
    headers = {"Authorization": f"Splunk {_config['token']}"}
    
    event = {
        "user": _config["user"],
        "workflow": _config["workflow"],
        "span_type": span_type,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        **details
    }
    
    payload = {
        "time": time.time(),
        "host": "code-server",
        "source": "genai_telemetry_sdk",
        "sourcetype": "genai:trace",
        "index": _config["index"],
        "event": event
    }
    
    try:
        # verify=False for lab environments with self-signed certs
        requests.post(url, headers=headers, json=payload, verify=False, timeout=5)
    except Exception as e:
        print(f"[TELEMETRY] Failed to send {span_type} event: {e}")

def trace_agent(agent_name, agent_type="general"):
    """Decorator to trace agent execution."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs_inner):
            trace_id = str(uuid.uuid4())
            start_time = time.time()
            print(f"[TELEMETRY] Starting Agent: {agent_name} (Type: {agent_type})")
            
            # Inject trace_id into context if needed (not implemented here)
            
            try:
                result = func(*args, **kwargs_inner)
                status = "success"
                return result
            except Exception as e:
                status = f"failed: {str(e)}"
                raise e
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                details = {
                    "trace_id": trace_id,
                    "agent_name": agent_name,
                    "agent_type": agent_type,
                    "duration_ms": duration_ms,
                    "status": status
                }
                send_telemetry("AGENT", details)
        return wrapper
    return decorator

def trace_tool(tool_name):
    """Decorator to trace tool execution."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs_inner):
            start_time = time.time()
            try:
                result = func(*args, **kwargs_inner)
                status = "success"
                return result
            except Exception as e:
                status = f"failed: {str(e)}"
                raise e
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                details = {
                    "tool_name": tool_name,
                    "duration_ms": duration_ms,
                    "status": status,
                    "tool_input": str(args[0]) if args else ""
                }
                send_telemetry("TOOL", details)
        return wrapper
    return decorator
