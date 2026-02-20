"""
Automated retry with exponential backoff for API rate limits and transient errors.
Used for OpenAI and other HTTP APIs.
"""
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Retryable OpenAI exceptions (rate limit, server errors, timeouts, connection)
try:
    from openai import (
        RateLimitError,
        APIStatusError,
        APITimeoutError,
        APIConnectionError,
    )
    RETRYABLE_EXCEPTIONS = (RateLimitError, APIStatusError, APITimeoutError, APIConnectionError)
except ImportError:
    RETRYABLE_EXCEPTIONS = ()

# HTTP status codes that are safe to retry (besides 429)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503}


def _status_code(error: Exception) -> Optional[int]:
    """Extract HTTP status code from an API error if present."""
    code = getattr(error, "status_code", None)
    if code is not None:
        return code
    resp = getattr(error, "response", None)
    return getattr(resp, "status_code", None) if resp else None


def is_retryable(error: Exception) -> bool:
    """Return True if the error is retryable (rate limit or transient)."""
    if not RETRYABLE_EXCEPTIONS or not isinstance(error, RETRYABLE_EXCEPTIONS):
        return False
    if isinstance(error, APIStatusError):
        return _status_code(error) in RETRYABLE_STATUS_CODES
    return True


def with_retry(
    callable_fn,
    *,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
):
    """
    Call callable_fn(); on rate limit or retryable errors, retry with exponential backoff.

    - callable_fn: no-arg callable that performs one API request (e.g. lambda: client.chat.completions.create(...))
    - max_retries: number of retries after the first attempt
    - initial_delay: first wait in seconds
    - max_delay: cap on wait between retries
    - exponential_base: multiplier for delay each retry

    Returns the result of callable_fn(). Raises the last exception if all retries fail.
    """
    last_error = None
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return callable_fn()
        except Exception as e:
            last_error = e
            if attempt == max_retries or not is_retryable(e):
                raise
            status = getattr(e, "status_code", None) if hasattr(e, "status_code") else None
            msg = str(e)
            if status == 429:
                logger.warning("API rate limit (429), retrying in %.1fs (attempt %d/%d)", delay, attempt + 1, max_retries + 1)
            else:
                logger.warning("API error (retryable): %s; retrying in %.1fs (attempt %d/%d)", msg[:200], delay, attempt + 1, max_retries + 1)
            time.sleep(delay)
            delay = min(delay * exponential_base, max_delay)
    raise last_error
