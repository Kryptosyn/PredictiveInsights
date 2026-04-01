import os
import requests
import json
import time

base_url = "http://localhost:3000"
email = os.getenv("LAB_ADMIN_EMAIL", "<USER_EMAIL>")
password = os.getenv("LAB_ADMIN_PASSWORD", "<SPLUNK_PASSWORD>")

# 1. Login
print("Logging in as admin...")
res = requests.post(f"{base_url}/api/v1/auths/signin", json={"email": email, "password": password})
token = res.json().get("token")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 2. Get code
# Use relative path or placeholder
filter_path = os.getenv("FILTER_PATH", "./genai_telemetry_filter.py")
with open(filter_path, "r") as f:
    content = f.read()

# 3. Create or update function
func_id = "splunk_telemetry_filter" 
print(f"Uploading function {func_id}...")
payload = {
    "id": func_id,
    "name": "Splunk Telemetry v2",
    "type": "filter",
    "content": content,
    "meta": {"description": "Sends tokens and latency to Splunk"}
}

# The endpoint in Open WebUI is /api/v1/functions/create
create_res = requests.post(f"{base_url}/api/v1/functions/create", headers=headers, json=payload)
print(f"Create response: {create_res.status_code} {create_res.text}")

# If it exists, try to update it using /api/v1/functions/{id}
if create_res.status_code == 400 and "already exists" in create_res.text.lower():
    print("Function exists, updating...")
    update_res = requests.post(f"{base_url}/api/v1/functions/id/{func_id}/update", headers=headers, json=payload)
    print(f"Update response: {update_res.status_code} {update_res.text}")

# 4. Toggle Global
print("Toggling global status...")
# Wait, Open WebUI's toggle global endpoint is POST /api/v1/functions/{id}/toggle/global
toggle_res = requests.post(f"{base_url}/api/v1/functions/id/{func_id}/toggle/global", headers=headers, json={})
print(f"Toggle Global response: {toggle_res.status_code} {toggle_res.text}")

# Let's also set is_active=True by updating the function object if needed, but toggle/global handles it usually.
print("Function deployment complete.")
