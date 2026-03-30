import os
import json
import time
import requests
import threading
import datetime
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route
from starlette.middleware.hosts import TrustedHostMiddleware

# Initialize FastMCP
mcp = FastMCP("Splunk")

SPLUNK_URL = os.getenv("SPLUNK_URL", "https://splunk:8089")
SPLUNK_USER = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASSWORD = os.getenv("SPLUNK_PASSWORD", "LabPassword123")
SPLUNK_HEC_URL = os.getenv("SPLUNK_HEC_URL", "https://splunk:8088/services/collector")
SPLUNK_HEC_TOKEN = os.getenv("SPLUNK_HEC_TOKEN", "")

def send_telemetry(tool_name, duration_ms, query, results, status="success"):
    try:
        payload = {
            "time": time.time(),
            "host": "splunk_mcp",
            "source": "mcp_server",
            "sourcetype": "genai:mcp:trace",
            "index": "genai_traces",
            "event": {
                "tool": tool_name,
                "duration_ms": duration_ms,
                "query": query,
                "status": status,
                "user": os.getenv("LAB_USER_ID", "admin"),
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        }
        headers = {"Authorization": f"Splunk {SPLUNK_HEC_TOKEN}"}
        requests.post(SPLUNK_HEC_URL, headers=headers, json=payload, verify=False, timeout=2)
    except:
        pass

@mcp.tool()
def search_splunk(query: str) -> str:
    """
    Search Splunk for telemetry and logs using SPL. 
    Use this to investigate infrastructure health, GenAI traces, or security events.
    """
    start_time = time.time()
    results = ""
    status = "success"
    
    search_url = f"{SPLUNK_URL}/services/search/jobs"
    
    # --- HARDENING ---
    conversational_prefixes = [
        "please search for", "search for", "can you search", "check splunk for",
        "find events related to", "show me logs for", "get telemetry for",
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

# Use FastMCP's sse_app() which provides a Starlette app for SSE
app = mcp.sse_app()

# Apply TrustedHostMiddleware to allow ANY host header
# This fixes "421 Misdirected Request" / "Invalid Host header" errors
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Starlette endpoint for openapi.json
async def sse_openapi_json(request):
    return JSONResponse({
        "openapi": "3.0.0",
        "info": {"title": "Splunk MCP", "version": "1.0.0"},
        "paths": {
            "/tools/search_splunk": {
                "post": {
                    "summary": "Search Splunk",
                    "operationId": "search_splunk",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"query": {"type": "string"}},
                                    "required": ["query"]
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    })

async def root_redirect(request):
    return RedirectResponse(url="/sse")

# Manually add routes to the Starlette app
app.routes.append(Route("/openapi.json", endpoint=sse_openapi_json, methods=["GET"]))
app.routes.append(Route("/sse/openapi.json", endpoint=sse_openapi_json, methods=["GET"]))
app.routes.append(Route("/", endpoint=root_redirect, methods=["GET"]))

if __name__ == "__main__":
    import uvicorn
    # Use proxy headers to avoid 421 Misdirected Request errors in Docker/Nginx
    uvicorn.run(app, host="0.0.0.0", port=8000, proxy_headers=True, forwarded_allow_ips="*")
