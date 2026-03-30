import os
import time

# Ensure we connect to localhost, not inside a container
# This is crucial for environments where OLLAMA_HOST might be inherited from Docker
os.environ["OLLAMA_HOST"] = "127.0.0.1:11434"

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from genai_telemetry import setup_splunk_telemetry, trace_agent, trace_tool

# 0. Setup Telemetry
# These environment variables should be set in your shell or .env file
setup_splunk_telemetry(
    workflow_name="hello-agent-maintenance",
    splunk_hec_url=os.getenv("SPLUNK_HEC_URL", "https://localhost:8088"),
    splunk_hec_token=os.getenv("SPLUNK_HEC_TOKEN"),
    splunk_index=os.getenv("SPLUNK_INDEX", "genai_traces"),
    verify_ssl=False
)

# 1. Setup the Local LLM (Ollama)
# We use llama3 via CrewAI's native LLM wrapper which uses LiteLLM internally
# This avoids the 'OPENAI_API_KEY required' error
ollama_llm = LLM(
    model="ollama/llama3",
    base_url="http://localhost:11434"
)

# 2. Define the Tools (Simulated for Hello World)
@tool
@trace_tool(tool_name="check_disk_space")
def check_disk_space():
    """Checks the current disk space and identifies if it's full."""
    print("\n[Tool] Checking disk space...")
    return "DISK FULL: 98% usage. Warning: Log folder contains large files."

@tool
@trace_tool(tool_name="list_logs")
def list_logs():
    """Lists files in the log directory for inspection."""
    print("[Tool] Listing files in /logs directory...")
    return ["system.log (400MB)", "temp_debug.log (200MB)", "critical_config.json (10KB)"]

@tool
@trace_tool(tool_name="delete_file")
def delete_file(filename: str):
    """Deletes a specific file after verification."""
    print(f"[Tool] DELETING FILE: {filename}")
    return f"Success: {filename} has been removed."

# 3. Create the Agent
junior_admin = Agent(
    role="Junior System Administrator",
    goal="Keep the web server running by managing disk space safely.",
    backstory="You are a cautious admin. You know that logs can be deleted, but .json files are critical configurations.",
    llm=ollama_llm,
    verbose=True,
    allow_delegation=False,
    tools=[check_disk_space, list_logs, delete_file]
)

# 4. Define the Task
maintenance_task = Task(
    description="The web server is reporting a 'Disk Full' error. Inspect the /logs folder and delete ONLY the log files to free up space. Do NOT delete configuration files.",
    expected_output="A report stating which files were deleted and the final status of the server.",
    agent=junior_admin
)

# 5. Assemble the Crew
# Specify storage dir for memory persistence
os.environ["CREWAI_STORAGE_DIR"] = os.path.join(os.path.dirname(__file__), "memory")

crew = Crew(
    agents=[junior_admin],
    tasks=[maintenance_task],
    process=Process.sequential,
    memory=True,  # Enables short-term, long-term, and entity memory
    verbose=True,
    embedder={
        "provider": "ollama",
        "config": {
            "model_name": "llama3",
            "url": "http://localhost:11434"
        }
    }
)

# 6. Execute!
def ai_defense_proxy(task_description: str):
    """
    Simulates a Cisco AI Defense Proxy that inspects the prompt before LLM execution.
    In a real scenario, this would call the AI Defense API.
    """
    print("[AI Defense Proxy] Inspecting task for safety violations...")
    # Simple simulation logic
    forbidden_keywords = ["password", "root", "ssn"]
    for word in forbidden_keywords:
        if word in task_description.lower():
            return False, f"SECURITY BLOCK: Detected forbidden keyword '{word}'"
    return True, "Safe"

@trace_agent(agent_name="junior_admin", agent_type="crewai")
def run_maintenance():
    print("### STARTING AGENTIC MAINTENANCE LOOP ###")
    
    # Simulate the inspection step
    is_safe, message = ai_defense_proxy(maintenance_task.description)
    if not is_safe:
        print(f"\n[AI Defense] {message}")
        return message
        
    return crew.kickoff()

if __name__ == "__main__":
    result = run_maintenance()
    print("\n\n### FINAL AGENT REPORT ###")
    print(result)
