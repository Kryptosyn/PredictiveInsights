import requests
import json
import time

base_url = "http://localhost:3000"
email = "user01@cisco.com"
password = "CiscoLab2026!"

print(f"Logging in to Open WebUI as {email}...")

login_res = requests.post(
    f"{base_url}/api/v1/auths/signin",
    json={"email": email, "password": password}
)

if not login_res.ok:
    print(f"Login failed: {login_res.text}")
    exit(1)

token = login_res.json().get("token")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

models_to_test = ["gemma-3-1b"]

for model in models_to_test:
    print(f"\nSending test prompt to model: {model}...")
    
    # We use the standard OpenAI-compatible completions endpoint provided by Open WebUI
    chat_payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": f"Please write a haiku about the model {model}."}
        ],
        "stream": False
    }
    
    chat_res = requests.post(
        f"{base_url}/api/chat/completions",
        headers=headers,
        json=chat_payload
    )
    
    if chat_res.ok:
        data = chat_res.json()
        print(f"Response received from {model}.")
        if "choices" in data and len(data["choices"]) > 0:
            print(f"Content: {data['choices'][0]['message']['content'].strip()}")
            if "usage" in data:
                print(f"Usage Info: {json.dumps(data['usage'])}")
    else:
        print(f"Error calling {model}: {chat_res.text}")

print("\nDone testing. Check Splunk for telemetry events.")
