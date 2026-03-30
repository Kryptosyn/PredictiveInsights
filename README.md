# GenAI Observability Pipeline

This project implements an automated GenAI Observability pipeline with secure remote access via Ngrok. It integrates Ollama for local LLM inference, Splunk for telemetry and dashboards, and a unified Nginx gateway for path-based routing.

## 🚀 Quick Start

### 1. Prerequisites
- **Docker Desktop**: Ensure Docker is running.
- **Ngrok Authtoken**: (Optional for remote access) The pipeline automatically attempts to discover your token from `~/.config/ngrok/ngrok.yml`.

### 2. Environment Setup
Copy the example environment file and configure your credentials. **Never commit your `.env` file.**
```bash
cp .env.example .env
```
Ensure the following variables are set in `.env`:
- `NGROK_AUTHTOKEN`: Your personal Ngrok token.
- `SPLUNK_PASSWORD`: Administrative password for Splunk.
- `SPLUNK_HEC_TOKEN`: Secure token for the HTTP Event Collector.


### 3. Start the Pipeline
```bash
docker-compose up -d
```
*Note: Splunk may take 3-4 minutes to reach a healthy state on the first startup.*

## 🌐 Accessing the Lab

Once the pipeline is running, all services are accessible via the **Unified Gateway** (Port 80):

- **Open WebUI**: [http://localhost/](http://localhost/)
- **Splunk Dashboard**: [http://localhost/splunk/](http://localhost/splunk/)
- **Web IDE**: [http://localhost/ide/](http://localhost/ide/)
- **Splunk MCP (Remote)**: [https://roosevelt-nonentreating-paler.ngrok-free.dev/mcp/sse](https://roosevelt-nonentreating-paler.ngrok-free.dev/mcp/sse)

### Secure Remote Access (Ngrok)
If Ngrok is enabled, use the public URL provided in the terminal or Ngrok dashboard:
`https://roosevelt-nonentreating-paler.ngrok-free.dev/`

## 📊 Observability Dashboard

The **GenAI Observability Platform** app is pre-configured in Splunk.

### Restoring the Dashboard
If the Splunk volumes are reset (`docker-compose down -v`), you can restore the dashboard and sample data by running:
1. Ensure Splunk is running: `docker-compose up -d splunk`
2. Sync the app configuration: `docker cp splunk/etc/apps/splunk_genai_observability splunk:/opt/splunk/etc/apps/`
3. Restart Splunk: `docker-compose restart splunk`

### Generating Sample Data
To populate the dashboard charts with mock telemetry:
```bash
# Set HEC URL and Token in your environment first
python3 repopulate_genai.py
```

## 🏗️ Architecture
- **Nginx Gateway**: Handles path-based routing (`/splunk/`, `/ide/`) and WebSocket upgrades.
- **Ngrok Tunnel**: Provides a secure HTTPS tunnel to the local Nginx gateway.
- **Splunk**: Log ingestion via HEC (Port 8088) and visualization.
- **Ollama**: Local LLM runner for gemma3:1b and other models.
