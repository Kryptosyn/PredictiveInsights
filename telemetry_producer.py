import time
import json
import random
import requests
import os

# Configuration from environment variables
SPLUNK_HOST = os.getenv('SPLUNK_HOST', 'localhost')
SPLUNK_PORT = os.getenv('SPLUNK_PORT', '8088')  # HEC port
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '')

def generate_nexus_telemetry():
    """Simulates Cisco Nexus 9000 telemetry."""
    return {
        "device": "nexus-9000-01",
        "timestamp": time.time(),
        "cpu_usage": random.uniform(10, 80),
        "memory_usage": random.uniform(20, 70),
        "interface_stats": [
            {"name": "eth1/1", "load": random.uniform(0, 100), "errors": random.randint(0, 5)},
            {"name": "eth1/2", "load": random.uniform(0, 100), "errors": random.randint(0, 5)}
        ],
        "temperature": random.uniform(35, 55)
    }

def generate_thousandeyes_data():
    """Simulates ThousandEyes synthetic path intelligence."""
    return {
        "test_name": "App-Performance-Check",
        "timestamp": time.time(),
        "latency_ms": random.uniform(5, 50),
        "loss_pct": random.uniform(0, 2),
        "jitter_ms": random.uniform(0.5, 5),
        "path_hops": random.randint(3, 8)
    }

def generate_isovalent_flows():
    """Simulates Cilium/Hubble eBPF flows."""
    return {
        "source": f"10.0.0.{random.randint(2, 254)}",
        "destination": "10.0.0.1",
        "protocol": "TCP",
        "verdict": random.choice(["FORWARDED", "DROPPED"]),
        "bytes": random.randint(100, 5000)
    }

def send_to_splunk(data, sourcetype):
    """Sends data to Splunk via HEC (HTTP Event Collector)."""
    # Note: In a real lab, you would use a valid token and SSL
    # For this simulation, we'll print if the token is missing
    if not SPLUNK_TOKEN:
        print(f"DEBUG [{sourcetype}]: {json.dumps(data)}")
        return

    url = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/services/collector"
    headers = {"Authorization": f"Splunk {SPLUNK_TOKEN}"}
    # Insert user tagging into the data object before sending
    data["user"] = os.getenv('LAB_USER_ID', 'shared')
    
    payload = {
        "event": data,
        "sourcetype": sourcetype
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        print(f"Sent {sourcetype} event to Splunk.")
    except Exception as e:
        print(f"Error sending to Splunk: {e}")

def generate_security_event():
    violations = [
        {"type": "PII Leakage", "detail": "Detected social security number in prompt"},
        {"type": "Prompt Injection", "detail": "Detected 'ignore previous instructions' pattern"},
        {"type": "Hallucination", "detail": "Agent attempted to access unauthorized /etc/shadow"}
    ]
    violation = random.choice(violations)
    
    return {
        "timestamp": time.time(),
        "event_type": "security_violation",
        "product": "Cisco AI Defense",
        "severity": "critical",
        "violation_type": violation["type"],
        "details": violation["detail"],
        "source_agent": "junior_admin"
    }

if __name__ == "__main__":
    print("Starting Telemetry Producer...")
    
    # Send one security event immediately for verification
    print("Sending initial AI Defense security event...")
    send_to_splunk(generate_security_event(), "cisco:ai:defense")
    
    while True:
        send_to_splunk(generate_nexus_telemetry(), "cisco:nexus:9000:telemetry")
        send_to_splunk(generate_thousandeyes_data(), "cisco:thousandeyes:path")
        send_to_splunk(generate_isovalent_flows(), "isovalent:hubble:flow")
        
        # Simulate occasional security discovery by AI Defense
        if random.random() < 0.3:
            send_to_splunk(generate_security_event(), "cisco:ai:defense")
            
        time.sleep(10)  # Generate data every 10 seconds
