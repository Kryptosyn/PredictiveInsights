# Walkthrough: Splunk MCP Server Integration

This module focuses on the **Agentic** phase of the lab. You will deploy a Model Context Protocol (MCP) server that allows Claude (or any MCP-compatible agent) to query Splunk Enterprise using natural language.

## 1. What is MCP?
The **Model Context Protocol (MCP)** is an open standard that enables AI models to securely access data and tools in external systems. Instead of hardcoding API integrations, the AI "discovers" the tools provided by the MCP server.

## 2. Setup the Splunk MCP Server

### A. Environment Configuration
The MCP server uses the Splunk Management API (Port 8089) for queries. Set these in your environment or within the Claude Desktop configuration:

```bash
export SPLUNK_URL="https://localhost:8089"
export SPLUNK_USER="admin"
export SPLUNK_PASSWORD="<SPLUNK_PASSWORD>"
```

### B. Install Dependencies
It is highly recommended to use a dedicated virtual environment to avoid dependency conflicts:
```bash
python3 -m venv venv
source venv/bin/activate
pip install fastmcp requests urllib3 mcp
```

### C. Run the Server
```bash
python3 mcp_server.py
```

### D. Local vs. Cloud LLM Telemetry
The MCP server can be configured to report telemetry for different LLM providers via environment variables. This is useful for comparing costs and performance between local models and cloud APIs:

- **Claude (Default)**: Reports estimated costs based on Anthropic's pay-per-token pricing.
- **Ollama / Local**: Reports **$0.00 cost** while still tracking token consumption and duration for performance analysis.

To switch providers in your `claude_desktop_config.json`:
```json
"env": {
  "LLM_PROVIDER": "ollama",
  "LLM_MODEL": "llama3"
}
```

## 3. Connecting to Claude
To use this with Claude Desktop:
1. Open your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`).
2. Add the Splunk MCP server with the absolute path to your virtual environment's Python and the server script:

```json
{
  "mcpServers": {
    "splunk": {
      "command": "<PROJECT_ROOT>/splunk_mcp/venv/bin/python3",
      "args": [
        "<PROJECT_ROOT>/splunk_mcp/mcp_server.py"
      ],
      "env": {
        "SPLUNK_URL": "https://localhost:8089",
        "SPLUNK_USER": "admin",
        "SPLUNK_PASSWORD": "<SPLUNK_PASSWORD>"
      }
    }
  }
}
```

## 4. Example Agentic Task
Once connected, you can ask Claude questions like:
*   *"Check the recent telemetry in Splunk for anomalies."*
*   *"What is the average CPU usage of nexus-9000-01 over the last hour?"*
*   *"Are there any interface errors on eth1/1?"*

Claude will automatically choose the `search_splunk` tool provided by the MCP server, execute the query, and provide a reasoned answer.

## 5. Cognition: Claude vs. Ollama
In the **Predictive Insights** phase, we used **Ollama (Llama3)** as the "brain" for the `predictive_engine.py` script. 

In this **Agentic Workflow** phase, **Claude (via Claude Desktop)** takes over that role:
- **Predictive Phase**: The script *defines* the logic; Ollama *provides* the inference.
- **Agentic Phase**: Claude *defines* the logic and *determines* which tools to use dynamically via the MCP server.

Essentially, Claude Desktop becomes your new primary interface for both **Observability** (data retrieval via MCP) and **Agency** (decision making and execution).

## 6. GenAI Observability & Cost Tracking
The Splunk MCP server includes built-in telemetry for the **GenAI Observability Dashboard**:
- **Automatic Tracing**: Every tool call sends telemetry to the `genai_traces` index.
- **Cost Estimation**: The server estimates token usage and calculates spend based on **Claude 3.5 Sonnet** pricing.
- **Metrics Tracked**: Input/Output tokens, Request Duration, Model Provider, and Total Cost.

This allows organizations to maintain governance and monitor the financial impact of agentic workflows in real-time.

## 8. Connecting to Open WebUI (Docker)

For large-scale lab environments, the Splunk MCP server is deployed within the **Unified Docker Stack**, allowing participants to access it via the **Open WebUI** chat interface.

### A. Containerized Architecture
The MCP server runs in the `splunk-mcp` container and is exposed internally at `http://splunk-mcp:8000/sse`. It is proxied through the Nginx Gateway for external access.

### B. Registering the Tool Server
To enable the Splunk tool in Open WebUI:
1.  **Access the Admin Panel**: Navigate to `http://localhost/` and login as an administrator.
2.  **Navigate to Integrations**: Go to **Settings** -> **Integrations**.
3.  **Add Connection**:
    - **Name**: `Splunk`
    - **URL**: `http://splunk-mcp:8000/sse`
    - **Type**: `MCP (Streamable HTTP)`
4.  **Verify**: Click the **Refresh** icon. A successful connection will return a green "Verified" status.

### C. Protocol Hardening (Technical Detail)
Open WebUI’s MCP implementation requires strict adherence to the SSE transport and JSON-RPC protocols. The Splunk MCP server includes specific hardening for this:
- **POST /sse Handler**: A dedicated handler satisfies Open WebUI's connection verification by returning a valid JSON-RPC 2.0 response.
- **TrustedHostMiddleware**: Allows connections from the internal Docker network and the Nginx proxy, preventing "421 Misdirected Request" errors.

## 9. Summary
By integrating MCP, you have moved from a **Fixed Pipeline** (where the script defines the logic) to an **Agentic Workflow** (where the AI discovers the tools it needs to solve a human goal). Whether using **Claude Desktop** or **Open WebUI**, the Splunk MCP server provides a unified interface for observability and automated operations.
