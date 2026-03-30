import os
import requests
import json
from pydantic import BaseModel, Field
from typing import Optional

class Tools:
    def __init__(self):
        # Service names from docker-compose
        self.splunk_url = os.getenv("SPLUNK_URL", "https://splunk:8089")
        self.splunk_user = os.getenv("SPLUNK_USER", "admin")
        self.splunk_password = os.getenv("SPLUNK_PASSWORD", "ChangedPassword123")

    def splunk_search(self, query: str = None, earliest_time: str = None, latest_time: str = None, **kwargs) -> str:
        """
        Search Splunk with RAW SPL ONLY (Splunk Search Language). 
        DO NOT pass natural language. 
        Example VALID queries: 'index=main', '| head 5', 'index=main sourcetype="cisco:nexus:9000:telemetry"'.
        """
        if not query:
            return "ERROR: Missing 'query' argument."

        import json
        import requests
        
        # Extract user identity from kwargs (passed by Open WebUI)
        __user__ = kwargs.get("__user__", {})
        user_identity = __user__.get("email", __user__.get("id", "unknown_user")) if __user__ else "anonymous"
        user_id = user_identity.split('@')[0] if '@' in user_identity else user_identity
        
        # --- AGGRESSIVE NL SANITIZER ---
        # 0. Strip leading punctuation
        query = query.lstrip("_: .-,[]").strip()
        
        # 1. Multi-Pass Prefix Stripping
        conversational_prefixes = [
            "search splunk for", "check splunk for", "check splunk", "what is the", "what are the", 
            "can you check", "tell me about", "look for", "latest telemetry for",
            "show me", "get me", "find", "search for", "telemetry for", "status of"
        ]
        q_lower = query.lower()
        for _ in range(3):
            for prefix in conversational_prefixes:
                if q_lower.startswith(prefix):
                    query = query[len(prefix):].strip()
                    query = query.lstrip("_: .-,[]").strip()
                    q_lower = query.lower()
                    break
        
        # 2. Global Stop-Word Removal (Removing "fluff" anywhere in the query)
        stop_words = ["telemetry", "latest", "recent", "my", "the", "events", "logs", "is", "about", "for", "please", "nexus 9000", "nexus-9000", "most"]
        for word in stop_words:
            import re
            query = re.sub(rf'\b{word}\b', '', query, flags=re.IGNORECASE).strip()
        
        # 3. Intelligent Device Mapping (Convert "nexus" to device wildcard)
        if "nexus" in query.lower() and "device=" not in query.lower():
            query = query.replace("nexus", "*nexus*").replace("Nexus", "*nexus*")
            if "index=" not in query:
                query = f'index=main device="*nexus*"'
        
        # 4. Final Fallback (If > 4 words with no SPL syntax, it is garbage NLP)
        if not query or len(query.strip()) < 3 or (len(query.split()) > 4 and "|" not in query and "=" not in query):
            query = "index=main | head 5"
            
        # 5. Force index=main and cleanup
        if query and "index=" not in query.lower() and not query.startswith("|"):
            query = f"index=main {query}"
            
        print(f"--- SPLUNK TOOL CALL ---")
        print(f"User: {user_id} | Final Query: {query}")
        # --- END HARDENING ---
        
        # Inject user field into the search results for audit/isolation
        tagging_query = f"{query} | eval user=\"{user_id}\""
        
        # Inject user field into the search results for audit/isolation
        tagging_query = f"{query} | eval user=\"{user_id}\""
        
        url = f"{self.splunk_url}/services/search/jobs"
        data = {
            "search": f"search {tagging_query}",
            "earliest_time": "-7d",
            "latest_time": "now",
            "exec_mode": "oneshot",
            "output_mode": "json"
        }
        
        try:
            # Note: verify=False is used because Splunk uses self-signed certs by default
            response = requests.post(
                url, 
                auth=(self.splunk_user, self.splunk_password), 
                data=data, 
                verify=False, 
                timeout=30
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            
            print(f"Result count: {len(results)}")
            
            if not results:
                # Differentiate between a clean search with no data and a possible configuration issue
                return (f"SUCCESS: Connected to Splunk as {user_id}. The search for '{query}' returned 0 results in the specified time range. "
                        f"TIP: If you are looking for Nexus data, ensure you use `index=main sourcetype=\"cisco:nexus:9000:telemetry\"`. "
                        f"If you recently started, telemetry might take 30-60 seconds to appear.")
            
            return json.dumps(results[:10], indent=2)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 400:
                try:
                    error_json = e.response.json()
                    messages = error_json.get("messages", [])
                    if messages:
                        error_text = messages[0].get("text", "Unknown syntax error")
                        return f"ERROR: Invalid SPL Syntax. Splunk rejected the query with: '{error_text}'. Please fix your query and try again. Ensure you start complex searches with 'index=main'."
                except Exception:
                    pass
            return f"ERROR: Failed to connect to Splunk: {str(e)}"
        except Exception as e:
            return f"ERROR: Unexpected error executing Splunk search: {str(e)}"
