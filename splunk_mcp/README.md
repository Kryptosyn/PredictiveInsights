# Splunk MCP Server

This directory contains the Model Context Protocol (MCP) server for Splunk Enterprise. It allows AI agents to interact with Splunk data using natural language.

## Prerequisites

- Python 3.10+
- Access to a Splunk Enterprise instance
- Splunk Management API credentials

## Installation

It is recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install fastmcp requests urllib3 mcp
```

## Configuration

The server uses the Splunk Management API (Port 8089). Set the following environment variables:

- `SPLUNK_URL`: The base URL of your Splunk instance (e.g., `https://localhost:8089`).
- `SPLUNK_USER`: Splunk username (e.g., `admin`).
- `SPLUNK_PASSWORD`: Splunk password (e.g., `ChangedPassword123`).

## Provided Tools

- `search_splunk(query, earliest_time, latest_time)`: Executes a raw SPL query.
- `get_device_telemetry(device_id)`: Fetches recent telemetry for a specific network device.

## Running the Server

```bash
python3 mcp_server.py
```
