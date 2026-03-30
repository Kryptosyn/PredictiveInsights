import os
import requests
import json
import time
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from genai_telemetry import setup_splunk_telemetry, trace_agent, trace_tool

# 0. Setup Telemetry
SPLUNK_HEC_URL = os.getenv("SPLUNK_HEC_URL", "http://127.0.0.1:8088")
SPLUNK_HEC_TOKEN = os.getenv("SPLUNK_HEC_TOKEN", "bb3b876d-a885-4820-8675-3fb520ac221d")
LAB_USER_ID = os.getenv("LAB_USER_ID", "default_analyst")

setup_splunk_telemetry(
    workflow_name="splunk-ai-analyst",
    splunk_hec_url=SPLUNK_HEC_URL,
    splunk_hec_token=SPLUNK_HEC_TOKEN,
    splunk_index="genai_traces",
    verify_ssl=False
)

# 1. Setup the Local LLM (Ollama)
ollama_llm = LLM(
    model="ollama/gemma3:1b",
    base_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
)

# 2. Define Splunk Tools
SPLUNK_MANAGEMENT_URL = os.getenv('SPLUNK_URL', 'http://127.0.0.1:8089')
SPLUNK_USER = os.getenv('SPLUNK_USER', 'admin')
SPLUNK_PASSWORD = os.getenv('SPLUNK_PASSWORD', 'ChangedPassword123')

@tool
@trace_tool(tool_name="splunk_search")
def splunk_search(query: str, earliest_time: str = "-24h", latest_time: str = "now"):
    """
    Executes a Splunk SPL query and returns the results. 
    Use this to find security violations, network drops, or performance metrics.
    """
    url = f"{SPLUNK_MANAGEMENT_URL}/services/search/jobs"
    data = {
        "search": f"search {query}",
        "earliest_time": earliest_time,
        "latest_time": latest_time,
        "exec_mode": "oneshot",
        "output_mode": "json"
    }
    try:
        response = requests.post(url, auth=(SPLUNK_USER, SPLUNK_PASSWORD), data=data, verify=False, timeout=20)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        return f"Error: {e}"

# 3. Create the Analyst Agent
analyst = Agent(
    role="Cisco AI Security & Network Analyst",
    goal="Analyze environment health and report issues across security and network data sources.",
    backstory="""You are an expert at interpreting Splunk data. 
    You look for:
    1. AI Security violations (cisco:ai:defense) like PII leakage, prompt injection, and unauthorized access.
    2. Network drops (isovalent:hubble:flow) specifically targeting gateway 10.0.0.1.
    3. Device performance issues (cisco:nexus:9000:telemetry).
    
    You provide structured, professional reports with clear 'Critical' and 'Warning' sections.""",
    llm=ollama_llm,
    verbose=True,
    allow_delegation=False,
    tools=[splunk_search]
)

@trace_agent(agent_name="splunk_analyst", agent_type="crewai")
def run_analysis(user_query: str):
    task = Task(
        description=user_query,
        expected_output="A structured environment health report with Critical and Warning sections, citing specific numbers and events from Splunk.",
        agent=analyst
    )
    
    crew = Crew(
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew.kickoff()

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "report any issues with my environment"
    
    print(f"\n### SPLUNK AI ANALYST (User: {LAB_USER_ID}) ###")
    print(f"Query: {query}\n")
    
    result = run_analysis(query)
    print("\n" + "="*50)
    print("FINAL ENVIRONMENT REPORT")
    print("="*50 + "\n")
    print(result)
