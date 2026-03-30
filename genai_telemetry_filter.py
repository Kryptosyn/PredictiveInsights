"""
GenAI Telemetry Filter for Open WebUI
Captures LLM metrics (tokens, latency, cost) and sends them to Splunk HEC.

IMPORTANT: Open WebUI uses `inlet` and `outlet` method names (NOT inbox/outbox).
"""
import os
import sys
import requests
import json
import datetime
import uuid
from pydantic import BaseModel, Field

# Top-level import confirmation
print("[TELEMETRY] genai_telemetry_filter module loaded", flush=True)


class Filter:
    class Valves(BaseModel):
        splunk_url: str = Field(
            default="https://splunk:8088/services/collector",
            description="Splunk HEC URL"
        )
            default=os.environ.get("SPLUNK_HEC_TOKEN", "bb3b876d-a885-4820-8675-3fb520ac221d"),
        cost_gemma3_1b: float = Field(default=0.15, description="Cost per 1M tokens for gemma3:1b")
        cost_phi3_mini: float = Field(default=0.05, description="Cost per 1M tokens for phi3:mini")
        cost_qwen2_5_7b: float = Field(default=0.30, description="Cost per 1M tokens for qwen2.5:7b")
        cost_qwen3_4b: float = Field(default=0.20, description="Cost per 1M tokens for qwen3:4b")
        cost_default: float = Field(default=0.10, description="Default cost per 1M tokens")

    def __init__(self):
        self.valves = self.Valves()
        print("[TELEMETRY] Filter.__init__ called", flush=True)

    def calculate_cost(self, model: str, total_tokens: int) -> float:
        model_l = model.lower()
        if "gemma3" in model_l or "gemma-3" in model_l:
            rate = self.valves.cost_gemma3_1b
        elif "phi3" in model_l or "phi-3" in model_l:
            rate = self.valves.cost_phi3_mini
        elif "qwen2.5" in model_l:
            rate = self.valves.cost_qwen2_5_7b
        elif "qwen3" in model_l:
            rate = self.valves.cost_qwen3_4b
        else:
            rate = self.valves.cost_default
        return (total_tokens / 1_000_000) * rate

    def send_to_splunk(self, event: dict):
        """Send event dict to Splunk HEC."""
        try:
            headers = {"Authorization": f"Splunk {self.valves.splunk_token}"}
            payload = {
                "time": datetime.datetime.now().timestamp(),
                "host": "open_webui",
                "source": "open_webui_filter",
                "sourcetype": "genai:trace",
                "index": "genai_traces",
                "event": event
            }
            resp = requests.post(
                self.valves.splunk_url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=5
            )
            print(f"[TELEMETRY] Splunk HEC response: {resp.status_code} {resp.text}", flush=True)
        except Exception as e:
            print(f"[TELEMETRY] ERROR sending to Splunk: {e}", flush=True)

    # ------------------------------------------------------------------ #
    # Open WebUI Filter API — correct method names are inlet / outlet     #
    # ------------------------------------------------------------------ #
    def inlet(self, body: dict, __user__: dict = None, **kwargs) -> dict:
        """Called BEFORE the LLM request is sent. Store start time."""
        print(f"[TELEMETRY] inlet triggered — model={body.get('model')} user={__user__}", flush=True)
        # Tag the body with a start timestamp we can read in outlet
        body["__telemetry_start__"] = datetime.datetime.now().timestamp()
        body["__telemetry_trace_id__"] = str(uuid.uuid4())
        return body

    def outlet(self, body: dict, __user__: dict = None, **kwargs) -> dict:
        """Called AFTER the LLM response is received. Capture metrics."""
        print(f"[TELEMETRY] outlet triggered — body_keys={list(body.keys())}", flush=True)

        try:
            model = body.get("model", "unknown")
            user_email = (__user__ or {}).get("email", "anonymous")
            user_id = user_email.split("@")[0] if "@" in user_email else user_email

            # Recover start time tagged in inlet
            start_ts = body.pop("__telemetry_start__", None)
            trace_id = body.pop("__telemetry_trace_id__", str(uuid.uuid4()))
            duration_ms = int((datetime.datetime.now().timestamp() - start_ts) * 1000) if start_ts else 0

            # --- Token extraction hierarchy ---
            # 1. OpenAI-compatible usage block
            usage = body.get("usage") or {}
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # 2. Ollama native fields inside messages[-1].info
            if total_tokens == 0 and body.get("messages"):
                last_msg = body["messages"][-1]
                info = last_msg.get("info") or {}
                prompt_tokens = info.get("prompt_eval_count", 0)
                completion_tokens = info.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens
                if info.get("total_duration"):
                    duration_ms = int(info["total_duration"] / 1_000_000)

            # 3. Char-count fallback (~4 chars / token)
            if total_tokens == 0 and body.get("messages"):
                msgs = body["messages"]
                completion_tokens = len(msgs[-1].get("content", "")) // 4
                prompt_tokens = sum(len(m.get("content", "")) for m in msgs[:-1]) // 4
                total_tokens = prompt_tokens + completion_tokens
                if duration_ms == 0:
                    duration_ms = 1500  # reasonable estimate

            cost = self.calculate_cost(model, total_tokens)

            event = {
                "trace_id": trace_id,
                "span_type": "LLM",
                "user": user_id,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "duration_ms": duration_ms,
                "cost": round(cost, 8),
                "gen_ai.usage.input_tokens": prompt_tokens,
                "gen_ai.usage.output_tokens": completion_tokens,
                "gen_ai.request.model": model,
                "gen_ai.system": "ollama",
                "gen_ai.client.duration": duration_ms,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

            print(f"[TELEMETRY] Sending event: {json.dumps(event)}", flush=True)
            self.send_to_splunk(event)

        except Exception as e:
            print(f"[TELEMETRY] outlet ERROR: {e}", flush=True)

        return body
