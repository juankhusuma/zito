from google import genai
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

# Create httpx client that bypasses proxy for Google APIs
http_client = httpx.Client(
    proxy=None,  # Explicitly disable proxy
    timeout=60.0
)

# Initialize Gemini client with custom HTTP client
client = genai.Client(
    api_key=os.getenv("GENAI_API_KEY"),
    http_options={'client': http_client}
)