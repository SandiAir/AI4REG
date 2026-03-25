"""LLM Client - Wrapper fuer Anthropic Claude API."""

import json
from typing import Any

import anthropic

from ngdai.core.config import get_settings
from ngdai.core.exceptions import LLMError


_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Singleton Anthropic-Client."""
    global _client
    if _client is None:
        settings = get_settings()
        api_key = settings.get_llm_api_key()
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY nicht konfiguriert. Setze NGDAI_ANTHROPIC_API_KEY in .env")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def extract_structured(
    text: str,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    max_tokens: int = 8192,
) -> dict[str, Any]:
    """Sendet Text an Claude und erwartet strukturiertes JSON zurueck.

    Args:
        text: Der zu analysierende Dokumenttext.
        system_prompt: System-Anweisung.
        user_prompt: User-Prompt mit Platzhalter {text} fuer den Dokumenttext.
        model: Modell-ID (default: extraction_model aus Config).
        max_tokens: Maximale Antwortlaenge.

    Returns:
        Geparster JSON-Dict.

    Raises:
        LLMError: Bei API- oder Parse-Fehlern.
    """
    settings = get_settings()
    model = model or settings.llm.extraction_model

    # Text in Prompt einsetzen
    final_user_prompt = user_prompt.replace("{text}", text)

    client = get_client()
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=settings.llm.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": final_user_prompt}],
        )
    except anthropic.APIError as e:
        raise LLMError(f"Anthropic API Fehler: {e}") from e

    # Response-Text extrahieren
    response_text = ""
    for block in response.content:
        if block.type == "text":
            response_text += block.text

    # JSON parsen (Claude gibt manchmal Markdown-Codeblocks zurueck)
    json_text = _extract_json(response_text)
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        raise LLMError(f"JSON-Parse-Fehler: {e}\nResponse: {response_text[:500]}") from e


def _extract_json(text: str) -> str:
    """Extrahiert JSON aus Text, auch wenn in Markdown-Codeblocks."""
    # Versuche ```json ... ``` Block
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return text[start:end].strip()
    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return text[start:end].strip()
    # Versuche direkt JSON (beginnt mit { oder [)
    text = text.strip()
    if text.startswith(("{", "[")):
        return text
    # Letzter Versuch: finde erstes { und letztes }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace >= 0 and last_brace > first_brace:
        return text[first_brace:last_brace + 1]
    return text
