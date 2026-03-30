import sqlite3
import os

DB_PATH = "/app/backend/data/webui.db"
TOOL_ID = "splunk_search"
SCRIPT_PATH = "/tmp/splunk_webui_tool.py"

# Correct admin user ID for micdemar@cisco.com
ADMIN_USER_ID = "3de0ac9a-a4c4-4ea3-b993-dacbd4906e71"

def update_tool():
    if not os.path.exists(SCRIPT_PATH):
        print(f"Error: {SCRIPT_PATH} not found")
        return

    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM tool WHERE id=?", (TOOL_ID,))
        if not cursor.fetchone():
            print(f"Tool {TOOL_ID} not found in database. Creating...")
            cursor.execute("INSERT INTO tool (id, user_id, name, content, meta, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                          (TOOL_ID, ADMIN_USER_ID, "Splunk Search", content, '{}', 0))
        else:
            print(f"Updating tool {TOOL_ID}...")
            cursor.execute("UPDATE tool SET content=?, user_id=? WHERE id=?", (content, ADMIN_USER_ID, TOOL_ID))
        
        conn.commit()
        print("Database Update Successful!")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_tool()
