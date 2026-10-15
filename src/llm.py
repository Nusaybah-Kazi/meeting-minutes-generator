import time

from groq import APIConnectionError, APIStatusError, Groq, RateLimitError

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
) -> str:
    """Send one prompt to Groq and return the text reply, retrying on transient errors."""
    model = model or config.LLM_MODEL
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    for attempt in range(retries):
        try:
            resp = get_client().chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except (RateLimitError, APIConnectionError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))
        except APIStatusError as e:
            if e.status_code >= 500 and attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise