from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .prompting import SYSTEM_PROMPT


def get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return api_key


def extract_json_object(text: str) -> Dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        return json.loads(snippet)

    raise ValueError(f"Failed to parse JSON object from model output:\n{text[:3000]}")


def call_llm_json_stream(
    prompt: str,
    model: str = "gpt-5.4-mini",
    api_url: str = "https://www.aiapikey.net/v1/chat/completions",
    timeout: float = 300.0,
    max_retries: int = 3,
    retry_backoff_base: float = 2.0,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    api_key = get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "stream": True,
    }

    timeout_cfg = httpx.Timeout(
        connect=min(30.0, timeout),
        read=timeout,
        write=min(60.0, timeout),
        pool=min(30.0, timeout),
    )

    llm_meta: Dict[str, Any] = {
        "model": model,
        "api_url": api_url,
        "timeout": timeout,
        "max_retries": max_retries,
        "attempts": [],
    }

    last_exc: Optional[Exception] = None
    retryable_statuses = {429, 500, 502, 503, 504, 524}

    for attempt in range(1, max_retries + 1):
        attempt_meta: Dict[str, Any] = {"attempt": attempt, "status": "started"}
        chunks: List[str] = []

        try:
            with httpx.Client(trust_env=False, http2=False, timeout=timeout_cfg) as client:
                with client.stream("POST", api_url, headers=headers, json=payload) as r:
                    attempt_meta["status_code"] = r.status_code
                    attempt_meta["response_headers"] = dict(r.headers)

                    if r.status_code != 200:
                        text = r.read().decode("utf-8", errors="replace")
                        attempt_meta["status"] = "http_error"
                        attempt_meta["response_text_preview"] = text[:5000]
                        llm_meta["attempts"].append(attempt_meta)

                        if r.status_code in retryable_statuses and attempt < max_retries:
                            time.sleep(retry_backoff_base ** (attempt - 1))
                            continue

                        raise RuntimeError(
                            f"LLM request failed with status {r.status_code}\nResponse: {text}"
                        )

                    for line in r.iter_lines():
                        if not line:
                            continue
                        if line == "data: [DONE]":
                            break
                        if not line.startswith("data: "):
                            continue

                        data = json.loads(line[6:])
                        choices = data.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            chunks.append(content)

            text = "".join(chunks)
            attempt_meta["raw_content_preview"] = text[:5000]
            model_json = extract_json_object(text)

            attempt_meta["status"] = "ok"
            llm_meta["attempts"].append(attempt_meta)
            llm_meta["status_code"] = 200
            llm_meta["response_headers"] = attempt_meta.get("response_headers", {})
            llm_meta["raw_content_preview"] = text[:5000]

            return model_json, llm_meta

        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
            last_exc = e
            attempt_meta["status"] = "timeout"
            attempt_meta["error_type"] = type(e).__name__
            attempt_meta["error_message"] = str(e)
            attempt_meta["partial_content_preview"] = "".join(chunks)[:5000]
            llm_meta["attempts"].append(attempt_meta)

            if attempt < max_retries:
                time.sleep(retry_backoff_base ** (attempt - 1))
                continue

        except httpx.HTTPError as e:
            last_exc = e
            attempt_meta["status"] = "httpx_error"
            attempt_meta["error_type"] = type(e).__name__
            attempt_meta["error_message"] = str(e)
            attempt_meta["partial_content_preview"] = "".join(chunks)[:5000]
            llm_meta["attempts"].append(attempt_meta)

            if attempt < max_retries:
                time.sleep(retry_backoff_base ** (attempt - 1))
                continue

        except Exception as e:
            last_exc = e
            attempt_meta["status"] = "other_error"
            attempt_meta["error_type"] = type(e).__name__
            attempt_meta["error_message"] = str(e)
            attempt_meta["partial_content_preview"] = "".join(chunks)[:5000]
            llm_meta["attempts"].append(attempt_meta)
            raise

    raise RuntimeError(
        f"LLM request failed after {max_retries} attempts. "
        f"Last error: {type(last_exc).__name__}: {last_exc}"
    ) from last_exc
