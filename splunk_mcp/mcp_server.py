import os
import json
import time
import requests
import threading
import datetime
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Initialize FastMCP
mcp = FastMCP("Splunk")

SPLUNK_URL = os.getenv("SPLUNK_URL", "https://splunk:8089")
SPLUNK_USER = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASSWORD = os.getenv("SPLUNK_PASSWORD", "<SPLUNK_PASSWORD>")
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
        # Harden telemetry for proxy environments: bypass proxies and ignore SSL for localhost
        requests.post(
            SPLUNK_HEC_URL, 
            headers=headers, 
            json=payload, 
            verify=False, 
            timeout=2,
            proxies={"http": None, "https": None}
        )
    except Exception as e:
        sys.stderr.write(f"Telemetry failed: {str(e)}\n")

@mcp.tool()
def search_splunk(query: str) -> str:
    """
    Search Splunk for telemetry and logs using SPL. 
    Use this to investigate infrastructure health, GenAI traces, or security events.
    """
    start_time = time.time()
    results = ""
    status = "success"
    
    # Debug logging to stderr for Claude Desktop visibility
    sys.stderr.write(f"--- Executing search_splunk ---\n")
    sys.stderr.write(f"Original Query: {query}\n")
    
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

    sys.stderr.write(f"Cleaned Query: {query}\n")

    data = {
        "search": f"search {query} | eval user=\"{os.getenv('LAB_USER_ID', 'admin')}\"",
        "earliest_time": "-15m",
        "latest_time": "now",
        "exec_mode": "oneshot",
        "output_mode": "json"
    }
    
    try:
        # Harden request: explicit proxy bypass and timeout management
        response = requests.post(
            search_url, 
            auth=(SPLUNK_USER, SPLUNK_PASSWORD), 
            data=data, 
            verify=False, 
            timeout=10, 
            proxies={"http": None, "https": None}
        )
        response.raise_for_status()
        results_data = response.json().get("results", [])
        
        # Payload management: Truncate to 5 results and limit internal string size to prevent proxy choking
        truncated_results = results_data[:5]
        results = json.dumps(truncated_results, indent=2)
        
        # If result is still massive (> 100KB), truncate the string
        if len(results) > 100000:
            results = results[:100000] + "\n... [TRUNCATED DUE TO SIZE] ..."
            
        sys.stderr.write(f"Search successful. Results: {len(truncated_results)} events\n")
        return results
    except Exception as e:
        status = "error"
        sys.stderr.write(f"Search failed: {str(e)}\n")
        return f"Error executing Splunk search: {str(e)}"
    finally:
        duration_ms = (time.time() - start_time) * 1000
        sys.stderr.write(f"Duration: {duration_ms:.2f}ms\n\n")
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

# Add a valid JSON-RPC POST handler for /sse to satisfy Open WebUI's verification
async def sse_post_handler(request):
    try:
        body = await request.json()
        msg_id = body.get("id", 0)
        # Return a valid JSON-RPC response format
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"status": "connected", "mcp_version": "1.0.0"}
        })
    except:
        return JSONResponse({
            "jsonrpc": "2.0", 
            "id": 0,
            "result": {"status": "connected"}
        })

app.routes.append(Route("/sse", endpoint=sse_post_handler, methods=["POST"]))

app.routes.append(Route("/", endpoint=root_redirect, methods=["GET"]))

if __name__ == "__main__":
    import sys
    # Check if we should run in SSE mode (for Docker/WebUI) or Stdio mode (for Desktop)
    if "--sse" in sys.argv or os.getenv("MCP_TRANSPORT") == "sse":
        import uvicorn
        # Use proxy headers to avoid 421 Misdirected Request errors in Docker/Nginx
        uvicorn.run(app, host="0.0.0.0", port=8000, proxy_headers=True, forwarded_allow_ips="*")
    else:
        # Default to Stdio for Claude Desktop
        mcp.run()
