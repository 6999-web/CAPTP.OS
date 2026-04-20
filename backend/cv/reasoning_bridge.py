from __future__ import annotations

from settings import settings


class ReasoningBridge:
    def __init__(self) -> None:
        self.enabled = settings.reasoning_enabled and bool(settings.reasoning_model and settings.reasoning_api_key)
        self._client = None
        if self.enabled:
            self._load_client()

    def _load_client(self) -> None:
        try:
            from openai import OpenAI

            kwargs = {"api_key": settings.reasoning_api_key}
            if settings.reasoning_base_url:
                kwargs["base_url"] = settings.reasoning_base_url
            self._client = OpenAI(**kwargs)
        except Exception:
            self.enabled = False
            self._client = None

    def enrich(self, structured_payload: dict, low_confidence: bool) -> str | None:
        if not self.enabled or not low_confidence or self._client is None:
            return None

        try:
            prompt = (
                "You are an assistant for police training. Expand the analysis in Chinese, "
                "but do not change factual detections. Keep result concise and actionable.\n\n"
                f"Structured detections: {structured_payload}"
            )
            response = self._client.chat.completions.create(
                model=settings.reasoning_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception:
            return None

