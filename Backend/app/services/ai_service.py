import hashlib
import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from redis import Redis

from app.config import settings


class AIService:
    def __init__(self, redis_client: Redis | None = None):
        self.redis_client = redis_client

    def analyze_alert(self, alert: dict) -> dict:
        prompt = self._build_analyze_alert_prompt(alert)
        cache_key = self._cache_key("analyze", prompt)

        cached = self._read_cache(cache_key)
        if cached:
            return cached

        response_content = self._call_llm(system_prompt=self._analysis_system_prompt(), user_prompt=prompt)
        parsed = self._parse_json_response(response_content)

        result = {
            "explanation": str(parsed.get("explanation", "")).strip(),
            "why_it_happened": str(parsed.get("why_it_happened", "")).strip(),
            "risk_level_reasoning": str(parsed.get("risk_level_reasoning", "")).strip(),
            "mitigation_steps": [str(step).strip() for step in parsed.get("mitigation_steps", []) if str(step).strip()],
        }

        if not result["mitigation_steps"]:
            result["mitigation_steps"] = [
                "Investigate source logs and isolate suspicious activity.",
                "Apply least-privilege and harden exposed services.",
                "Monitor for repeated indicators after mitigation.",
            ]

        self._write_cache(cache_key, result)
        return result

    def chat(self, query: str) -> str:
        prompt = (
            "You are SecuWatch assistant. Answer security questions clearly with practical steps. "
            "Keep answers concise and actionable.\n\n"
            f"User question: {query.strip()}"
        )

        cache_key = self._cache_key("chat", prompt)
        cached = self._read_cache(cache_key)
        if cached and "response" in cached:
            return str(cached["response"])

        response = self._call_llm(system_prompt=self._chat_system_prompt(), user_prompt=prompt)
        clean_response = response.strip()

        self._write_cache(cache_key, {"response": clean_response})
        return clean_response

    @staticmethod
    def _analysis_system_prompt() -> str:
        return (
            "You are a cybersecurity analyst assistant. "
            "Always return strictly valid JSON with keys: "
            "explanation, why_it_happened, risk_level_reasoning, mitigation_steps. "
            "mitigation_steps must be an array of actionable strings."
        )

    @staticmethod
    def _chat_system_prompt() -> str:
        return (
            "You are a cybersecurity assistant. Provide safe, practical, and defensive guidance "
            "for security operations and hardening."
        )

    @staticmethod
    def _build_analyze_alert_prompt(alert: dict) -> str:
        created_at = alert.get("created_at")
        if isinstance(created_at, datetime):
            created_at_value = created_at.isoformat()
        else:
            created_at_value = str(created_at) if created_at is not None else "unknown"

        return (
            "Analyze this security alert and explain it in simple terms.\n"
            "Alert data:\n"
            f"- alert_id: {alert.get('id', 'unknown')}\n"
            f"- device_id: {alert.get('device_id', 'unknown')}\n"
            f"- alert_type: {alert.get('type', 'unknown')}\n"
            f"- description: {alert.get('description', '')}\n"
            f"- severity: {alert.get('severity', 'unknown')}\n"
            f"- created_at: {created_at_value}\n\n"
            "Required output JSON format:\n"
            "{\n"
            '  "explanation": "...",\n'
            '  "why_it_happened": "...",\n'
            '  "risk_level_reasoning": "...",\n'
            '  "mitigation_steps": ["step 1", "step 2", "step 3"]\n'
            "}\n"
            "Focus on actionable and defensive guidance only."
        )

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        api_key = settings.gemini_api_key or settings.llm_api_key
        if not api_key:
            raise ValueError("LLM API key not configured")

        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        request = Request(
            settings.llm_api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        timeout_seconds = max(1, settings.llm_timeout_seconds)
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"LLM request failed with status {exc.code}: {detail}") from exc
        except URLError as exc:
            raise ValueError(f"LLM request failed: {exc.reason}") from exc

        data = json.loads(body)
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("LLM returned no choices")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise ValueError("LLM returned empty response")

        return content

    @staticmethod
    def _parse_json_response(content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(content[start : end + 1])
            raise ValueError("LLM did not return valid JSON")

    @staticmethod
    def _cache_key(prefix: str, value: str) -> str:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return f"ai:{prefix}:{digest}"

    def _read_cache(self, key: str) -> dict | None:
        if not self.redis_client or settings.ai_cache_ttl_seconds <= 0:
            return None

        cached = self.redis_client.get(key)
        if not cached:
            return None

        if isinstance(cached, bytes):
            cached_value = cached.decode("utf-8", errors="ignore")
        elif isinstance(cached, str):
            cached_value = cached
        else:
            return None

        try:
            return json.loads(cached_value)
        except json.JSONDecodeError:
            return None

    def _write_cache(self, key: str, value: dict) -> None:
        if not self.redis_client or settings.ai_cache_ttl_seconds <= 0:
            return

        self.redis_client.setex(key, settings.ai_cache_ttl_seconds, json.dumps(value))
