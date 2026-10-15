import time

from groq import (
    APIConnectionError,
    APIStatusError,
    BadRequestError,
    Groq,
    RateLimitError,
)

from src import config

_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=config.require_api_key())
    return _client


def chat(
    prompt: str,
    system: str = "You are a helpful assistant.",
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    retries: int = 3,
    json_mode: bool = False,
) -> str:
    """Send one prompt to Groq and return the text reply, retrying on transient errors."""
    model = model or config.LLM_MODEL
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    for attempt in range(retries):
        kwargs = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            resp = get_client().chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except BadRequestError:
            if json_mode:
                json_mode = False  # JSON mode rejected; retry as plain text
                continue
            raise
        except (RateLimitError, APIConnectionError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))
        except APIStatusError as e:
            if e.status_code >= 500 and attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
    raise RuntimeError("Groq request failed after retries.")