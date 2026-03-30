# Implementation Plan - Fix Token Cost in Splunk Dashboard

The user is reporting that "token cost" is not showing in the Splunk dashboard for the "Predictive Insights" project. My investigation reveals two primary issues:

1.  **Llama3 Support**: The `llama3` model (executed via Ollama) is missing from the `genai_model_pricing.csv` lookup table.
2.  **Claude Mismatch**: There is a naming mismatch between the Splunk MCP server (`claude-3-5-sonnet`) and the Splunk lookup table (`claude-3.5-sonnet`), which breaks cost simulation for the MCP server.

> [!NOTE]
> **Verification Results**: I've verified this behavior with a test script. While `claude-3.5-sonnet` works correctly, `claude-3-5-sonnet` fails to calculate cost in the dashboard because the lookup doesn't match.

> [!TIP]
> **On-Premise Cost Modeling**: While Ollama runs locally with near-zero marginal cost, we typically model a "Shadow Cost" (simulated cloud pricing) in the dashboard to:
> 1.  **Demonstrate ROI**: Show the massive savings achieved by running locally vs. in the cloud.
> 2.  **Internal Chargebacks**: Simulate how an enterprise might allocate local compute costs (hardware/electricity).
> 3.  **Dashboard Health**: Ensure the visualization panels are populated and not showing empty values.

## User Review Required
- **Cost Value**: Should we use a "Shadow Cost" (e.g., $0.00005/1k) to show what it *would* have cost, or set it to $0 to reflect actual local consumption? My default plan uses the former to make the dashboard more informative.

### Splunk Configuration
#### [MODIFY] [genai_model_pricing.csv](file:///Users/micdemar/Library/CloudStorage/OneDrive-Cisco/Predictive%20Insights/splunk/etc/apps/splunk_genai_observability/lookups/genai_model_pricing.csv)
- Add an entry for `llama3` to ensure the `genai_cost_lookup` macro can retrieve pricing information.
- I will use a simulated cost of `$0.00005` per 1k tokens (matching Llama 3.1 8B) to ensure the dashboard displays data while acknowledging it's a local model.
- Add an alias/entry for `claude-3-5-sonnet` (with hyphens) to match the naming used in the `mcp_server.py`.

```diff
+ llama3,ollama,0.00005,0.00005,8192,4096
+ claude-3-5-sonnet,anthropic,0.003,0.015,200000,8192
```

### Predictive Engine
#### [MODIFY] [predictive_engine.py](file:///Users/micdemar/Library/CloudStorage/OneDrive-Cisco/Predictive%20Insights/predictive_engine.py)
- Update the `timestamp` field in the `metrics` dictionary to use ISO 8601 string format to match Splunk's expected format.

```diff
-             "timestamp": time.time()
+             "timestamp": datetime.datetime.now().isoformat()
```

## Verification Plan

### Automated Verification
- Run `python3 predictive_engine.py` to generate a new telemetry event.
- Verify the script output prints "GenAI Observability metrics sent to Splunk".

### Manual Verification
1. Access Splunk at `http://localhost:8000` (User: `admin` / Password: `ChangedPassword123`).
2. Navigate to the **GenAI Observability** app.
3. Open the **Cost Management** dashboard.
4. Verify that **Total Cost** and **Input vs Output Token Cost** panels now display data for the `llama3` model.
5. (Optional) Run the following SPL in the search bar to verify field extraction:
   ```splunk
   `genai_llm_spans` model_name="llama3" | `genai_cost_lookup` | `genai_calculate_cost` | table _time, model_name, input_tokens, output_tokens, estimated_cost
   ```
