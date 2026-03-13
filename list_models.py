import os

from google import genai


api_key = os.getenv("GEMINI_API_KEY", "").strip()
if not api_key:
    raise SystemExit("Missing GEMINI_API_KEY environment variable.")

client = genai.Client(api_key=api_key)
for m in client.models.list():
    name = m.name
    if any(k in name.lower() for k in ["flash", "imagen", "image", "nano"]):
        print(name)
