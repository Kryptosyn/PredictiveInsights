import requests
import json
import urllib3

urllib3.disable_warnings()

url = "https://localhost:8089/services/search/jobs"
auth = ("admin", "ChangedPassword123")

queries_to_test = [
    "search | timeorder desc | limit 10 | eval user=\"anonymous\"",
    "search index=main | stats values(source) as source_types | eval user=\"anonymous\""
]

for q in queries_to_test:
    data = {
        "search": q,
        "earliest_time": "-7d",
        "latest_time": "now",
        "exec_mode": "oneshot",
        "output_mode": "json"
    }

    print(f"Testing Query: {q}")
    resp = requests.post(url, auth=auth, data=data, verify=False, proxies={"http": None, "https": None})
    print(f"  -> Status: {resp.status_code}")
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        print(f"  -> Returned {len(results)} results")
    else:
        print(f"  -> Error Body: {resp.text}")
