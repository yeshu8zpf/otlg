import os, httpx
from openai import OpenAI, DefaultHttpxClient


http_client = httpx.Client(
    trust_env=False,
    http2=False,
    timeout=30.0,
    follow_redirects=True,
)
client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
    http_client=http_client
)

models = client.models.list()
print(models)