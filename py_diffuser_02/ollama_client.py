"""Optional local Ollama prompt enhancement."""

import requests

from . import config


def enhance_prompt(prompt: str, log_func) -> str:
    """Turn a short user prompt into a concise photorealistic SD prompt.

    If Ollama is disabled, unavailable, or returns an unusable response, the
    original prompt is returned so image generation can continue.
    """
    if not config.USE_OLLAMA:
        return prompt

    try:
        log_func(f"Sending prompt to Ollama ({config.OLLAMA_MODEL}) for enhancement...")

        payload = {
            "model": config.OLLAMA_MODEL,
            "prompt": (
                config.PHOTOREALISTIC_SYSTEM_PROMPT
                + "\n\nPrompt:\n"
                + prompt
            ),
            "stream": False,
        }

        response = requests.post(config.OLLAMA_URL, json=payload, timeout=120)

        if response.status_code != 200:
            log_func(
                f"Ollama returned HTTP {response.status_code}; using original prompt."
            )
            return prompt

        enhanced = response.json().get("response", "").strip()
        if not enhanced:
            log_func("Ollama returned an empty response; using original prompt.")
            return prompt

        log_func("Ollama enhancement complete.")
        return enhanced

    except Exception as exc:
        log_func(f"Ollama request failed: {exc}; using original prompt.")
        return prompt
