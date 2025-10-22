from dotenv import load_dotenv
import os

load_dotenv()

# CRITICAL: Unset proxy environment variables BEFORE importing genai
# This prevents httpx (used internally by genai) from using the CS UI proxy
# which blocks access to googleapis.com
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
saved_proxies = {}

for var in proxy_vars:
    if var in os.environ:
        saved_proxies[var] = os.environ[var]
        del os.environ[var]

# Now import genai after clearing proxy settings
from google import genai

# Create client (will use direct connection, no proxy)
client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))