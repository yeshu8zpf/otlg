from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx


API_URL = "https://www.aiapikey.net/v1/chat/completions"
MODEL = "claude-haiku-4-5"


def get_api_key(k='claude') -> str:
    if k == 'gpt':
        api_key = os.getenv("OPENAI_API_KEY")
    elif k == 'claude':
        api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise RuntimeError("API_KEY is not set.")
    return api_key


def read_prompt_file() -> str:
    candidates = [
        # Path("/root/ontology/prompt_nbd"),
        Path("/root/ontology/prompt"),
        Path("/root/ontology/prompt.txt"),
        Path("/root/ontology/prompt.md"),
        Path("/root/ontology/outputs/iswc/prompt.md"),
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            text = p.read_text(encoding="utf-8", errors="ignore")
            print(f"[INFO] loaded prompt from: {p}")
            print(f"[INFO] prompt chars: {len(text)}")
            return text
    raise FileNotFoundError(
        "Cannot find prompt file. Checked: "
        + ", ".join(str(p) for p in candidates)
    )


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


def build_payload(prompt: str, stream: bool) -> Dict[str, Any]:
    return {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Output valid JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.0,
        "stream": stream,
    }


def test_non_stream(prompt: str, http2: bool) -> None:
    print(f"\n===== TEST non-stream | http2={http2} =====")
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    payload = build_payload(prompt, stream=False)

    timeout_cfg = httpx.Timeout(connect=300.0, read=300.0, write=60.0, pool=30.0)

    with httpx.Client(trust_env=False, http2=http2, timeout=timeout_cfg) as client:
        resp = client.post(API_URL, headers=headers, json=payload)
        print("[INFO] status:", resp.status_code)
        print("[INFO] headers:", dict(resp.headers))

        text = resp.text
        print("[INFO] response preview:", text[:1000])

        resp.raise_for_status()

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print("[INFO] content preview:", content[:1000])

        try:
            parsed = extract_json_object(content)
            print("[OK] JSON parsed, top-level type:", type(parsed).__name__)
            if isinstance(parsed, dict):
                print("[OK] top-level keys:", list(parsed.keys())[:30])
        except Exception as e:
            print("[WARN] content is not parseable JSON:", repr(e))


def test_stream(prompt: str, http2: bool) -> None:
    print(f"\n===== TEST stream | http2={http2} =====")
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    payload = build_payload(prompt, stream=True)

    timeout_cfg = httpx.Timeout(connect=300.0, read=300.0, write=60.0, pool=30.0)

    chunks = []
    line_count = 0
    content_chunk_count = 0
    done_seen = False

    with httpx.Client(trust_env=False, http2=http2, timeout=timeout_cfg) as client:
        with client.stream("POST", API_URL, headers=headers, json=payload) as resp:
            print("[INFO] status:", resp.status_code)
            print("[INFO] headers:", dict(resp.headers))
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue

                line_count += 1

                if line == "data: [DONE]":
                    done_seen = True
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
                    content_chunk_count += 1

    text = "".join(chunks)

    print("[INFO] total lines:", line_count)
    print("[INFO] content chunks:", content_chunk_count)
    print("[INFO] done seen:", done_seen)
    print("[INFO] assembled chars:", len(text))
    print("[INFO] assembled preview (head):", text[:500])
    print("[INFO] assembled preview (tail):", text[-500:])

    try:
        parsed = extract_json_object(text)
        print("[OK] JSON parsed, top-level type:", type(parsed).__name__)
        if isinstance(parsed, dict):
            print("[OK] top-level keys:", list(parsed.keys())[:30])
    except Exception as e:
        print("[WARN] streamed content is not parseable JSON:", repr(e))

def main() -> None:
    prompt = read_prompt_file()

    try:
        test_non_stream(prompt, http2=False)
    except Exception as e:
        print("[FAIL] non-stream http1.1:", repr(e))

    # try:
    #     test_non_stream(prompt, http2=True)
    # except Exception as e:
    #     print("[FAIL] non-stream http2:", repr(e))

    try:
        test_stream(prompt, http2=False)
    except Exception as e:
        print("[FAIL] stream http1.1:", repr(e))

    # try:
    #     test_stream(prompt, http2=True)
    # except Exception as e:
    #     print("[FAIL] stream http2:", repr(e))


if __name__ == "__main__":
    main()