import sqlite3
import time
import uuid

# Define the filter content
with open("/tmp/genai_telemetry_filter.py", "r") as f:
    content = f.read()

# Connect to the database inside the container
db_path = "/app/backend/data/webui.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get admin user id 
c.execute("SELECT id FROM user WHERE role='admin' LIMIT 1;")
res = c.fetchone()
if res:
    user_id = res[0]
else:
    user_id = str(uuid.uuid4()) # Fallback

func_id = "splunk_telemetry_filter"
now = int(time.time())

# Ensure table schema is exactly what the DB expects
try:
    c.execute("""
    INSERT OR REPLACE INTO function 
    (id, user_id, name, type, content, meta, created_at, updated_at, valves, is_active, is_global)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        func_id, 
        user_id, 
        "Splunk Telemetry",
        "filter",
        content,
        "{}", # meta
        now,
        now,
        "{}", # empty valves (uses defaults)
        1, # is_active
        1  # is_global
    ))
    conn.commit()
    print("Successfully injected Splunk Telemetry filter into Open WebUI database!")
except Exception as e:
    print(f"Error injecting into DB: {e}")
finally:
    conn.close()
