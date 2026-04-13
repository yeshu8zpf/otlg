import os
import httpx

url = "https://www.aiapikey.net"
headers = {
    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
    "Content-Type": "application/json",
}
payload = {
    "model": "gpt-5.4-mini",
    "messages": [
        {"role": "user", "content": "tell me your name"}
    ]
}

with httpx.Client(trust_env=False, http2=False, timeout=60.0) as client:
    r = client.post(url, headers=headers, json=payload)
    print(r.status_code)
    print(r.text)