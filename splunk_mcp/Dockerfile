FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY mcp_server.py .

# Environment variables (defaults)
ENV SPLUNK_URL=https://splunk:8089
ENV SPLUNK_USER=admin
ENV SPLUNK_PASSWORD=ChangedPassword123
ENV SPLUNK_HEC_TOKEN=
ENV LLM_PROVIDER=ollama
ENV LLM_MODEL=gemma3:1b

# Expose SSE port (FastMCP default)
EXPOSE 8000

CMD ["python", "mcp_server.py", "--sse"]
