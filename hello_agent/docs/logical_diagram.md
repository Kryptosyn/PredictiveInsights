# Logical Diagram: The Agentic Loop

This diagram illustrates how the **Junior Admin Agent** operates compared to a traditional scheduled script.

```mermaid
graph TD
    subgraph "Environment (The Web Server)"
        SRV["Server Status"]
        DSK["Disk / Logs Folder"]
    end

    subgraph "The Agent (CrewAI + Ollama)"
        direction TB
        G[Goal: Keep Server Running]
        P[Reasoning: 'Is the disk full? Is this a log?']
        
        subgraph "Tools"
            T1[Check_Disk_Space]
            T2[Identify_File_Type]
            T3[Delete_File]
        end
    end

    %% Perception
    DSK -- "Observation" --> P
    SRV -- "Health Check" --> P

    %% Cognition
    G --> P
    P -- "Decision" --> T1
    P -- "Decision" --> T2
    P -- "Decision" --> T3

    %% Action
    T1 -.-> DSK
    T3 -.-> DSK
    
    %% Result
    DSK -- "Success/Failure" --> P
```

### Key Differentiators:
1.  **Goal Driven**: The agent starts with the *outcome* (Server Running) and works backward.
2.  **State Aware**: It checks the environment *before* acting using Tools.
3.  **Corrective Feedback**: If a deletion doesn't fix the server, the agent can try a different "tool" or notify a human.
