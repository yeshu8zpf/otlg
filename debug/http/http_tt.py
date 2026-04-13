import httpx
import os

url = "https://www.aiapikey.net/v1/models"
headers = {
    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
}

# 1) 先完全不读环境变量
with httpx.Client(trust_env=False, timeout=30.0, http2=False) as client:
    r = client.get(url, headers=headers)
    print("http2=False status:", r.status_code)
    print(r.text[:500])

# 2) 再试 http2=True
with httpx.Client(trust_env=False, timeout=30.0, http2=True) as client:
    r = client.get(url, headers=headers)
    print("http2=True status:", r.status_code)
    print(r.text[:500])