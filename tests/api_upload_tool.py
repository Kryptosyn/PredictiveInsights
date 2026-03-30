import requests
import json
import os

WEBUI_URL = "http://localhost:3000/api/v1/tools"
# The token we used earlier
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjNkZTBhYzlhLWE0YzQtNGVhMy1iOTkzLWRhY2JkNDkwNmU3MSIsImV4cCI6MTc3NjgwNzI4NSwianRpIjoiZmU4MzYyYjEtMzNmYi00MmI1LTliNDktNWExYTlhMTU3MjZlIn0.0Sj63L1G5v_366Y7E_M9c2i5m_6_H8W0HqY3I9m1U0U"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def get_tool_script():
    with open("splunk_webui_tool.py", "r") as f:
        return f.read()

def upload_tool():
    script = get_tool_script()
    
    payload = {
        "id": "splunk_search",
        "name": "Splunk Network & Security Search",
        "meta": {
            "description": "Searches Splunk for Nexus telemetry and security events.",
            "manifest": {
                "title": "Splunk Search",
                "description": "Real-time visibility into the lab environment."
            }
        },
        "content": script
    }

    # Try to find if it exists
    resp = requests.get(WEBUI_URL, headers=headers)
    tools = resp.json()
    
    existing_tool = next((t for t in tools if t['id'] == 'splunk_search'), None)
    
    if existing_tool:
        print(f"Updating existing tool: splunk_search")
        update_url = f"{WEBUI_URL}/id/splunk_search/update"
        resp = requests.post(update_url, headers=headers, json=payload)
    else:
        print(f"Creating new tool: splunk_search")
        create_url = f"{WEBUI_URL}/create"
        resp = requests.post(create_url, headers=headers, json=payload)
    
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    upload_tool()
