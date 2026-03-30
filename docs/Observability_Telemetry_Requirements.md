# GenAI Observability & Telemetry Requirements

This document outlines the architectural requirements and the checklist of tasks required to fully instrument Open WebUI with Splunk's GenAI Observability App.

## 1. Core Objectives
The primary goal is to provide a transparent, real-time dashboard reflecting the performance, cost, and reliability of the generative AI models used in the Predictive Digital Twin lab.

### Key Metrics to Capture:
*   **LLM Latency (`duration_ms`)**: Processing time for each prompt.
*   **Token Consumption**: Prompt (input) tokens and Completion (output) tokens, driving capacity planning.
*   **Cost Management (`cost`)**: Estimated financial impact per model usage, allowing comparison between lightweight (e.g., `phi3:mini`) and heavier models.
*   **Retrieval-Augmented Generation (RAG) Analytics**: Performance and relevance tracking for document-grounded responses.
*   **Hallucination Detection**: Automated scoring of LLM outputs to measure factual accuracy and contextual relevance.
*   **Agent & Tool Monitoring**: Tracking autonomous executions (like the `junior_admin` synthetic agent) to visualize task durations and tool success/failure rates.

## 2. Technical Requirements

### The Telemetry Pipeline (Open WebUI Filter)
A custom Python filter must be integrated into Open WebUI. It will act as the telemetry producer:
1.  **Intercept**: Hook into the `outbox` pipeline to analyze Ollama's response stream.
2.  **Extract**: Pull `user.email`, `body.model`, `prompt_eval_count`, `eval_count`, and `total_duration`.
3.  **Synthesize Costs**: Apply a hardcoded or configured cost-per-token mapping based on the `model` name.
4.  **Format**: Construct JSON payloads matching Splunk's expectations (`index=genai_traces`, `sourcetype=genai:trace`, `span_type=LLM`).
5.  **Transmit**: Asynchronously POST the payload to the Splunk HTTP Event Collector (HEC) at `https://splunk:8088/services/collector`.

### Advanced Analytics
1.  **RAG Tracing**:
    *   Requirement: Hook into Open WebUI's document retrieval system.
    *   Action: Emit a `span_type="RETRIEVER"` event containing `documents_retrieved` and `duration_ms` tied to the parent LLM `trace_id`.
2.  **Hallucination Scoring**:
    *   Requirement: Implement a secondary evaluation pipeline.
    *   Action: Upon receiving a final response, trigger a fast evaluator model (e.g., `phi3:mini`) to score the relevance/fluidity of the generated text against the original prompt context. Embed this as `hallucination_score` in a `span_type="EVALUATION"` trace.
3.  **Agent Monitoring**:
    *   Requirement: Instrument the synthetic `junior_admin` agent.
    *   Action: Use the `genai_telemetry.py` module to decorate the agent's logic. Emit `span_type="AGENT"` and `span_type="TOOL"` traces carrying the `agent_name`, `tool_name`, and execution metrics.

## 3. Tasks Performed (Execution Checklist)

*   [ ] **1. Model Provisioning**: Deploy at least two additional models to Ollama (e.g., `phi3:mini`, `qwen2:0.5b`) to provide a baseline for cost and latency comparison against `gemma3:1b`.
*   [ ] **2. Telemetry Filter Development**: Author the Python script (`genai_telemetry_filter.py`) and upload it to Open WebUI's Workspace functions.
*   [ ] **3. Metric Verification**: Perform test prompts across all 3 models and verify `genai_traces` index in Splunk accurately reflects token counts, costs, and differing latencies.
*   [ ] **4. RAG Implementation**: Configure the filter to detect document uploads/retrieval triggers and emit `RETRIEVER` spans.
*   [ ] **5. Hallucination Evaluator**: Configure the background evaluation prompt and verify the population of the Hallucination Detection dashboard.
*   [ ] **6. Agent Monitoring Integration**: Integrate the `genai_telemetry.py` decorators into the `junior_admin` synthetic agent script to pipe `AGENT` spans to Splunk.
*   [ ] **7. Dashboard Finalization**: Confirm all tabs in the Splunk Observability App (**Overview, LLM Performance, Cost Management, Agents and Tools, RAG Analytics, Hallucination Detection**) are actively receiving and correctly displaying the telemetry data.
