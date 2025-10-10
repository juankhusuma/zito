from supabase import create_client
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

client = create_client(
    supabase_key=os.getenv("SUPABASE_ANON_KEY"),
    supabase_url=os.getenv("SUPABASE_URL"),
)

# Configure httpx client to use proxy explicitly
proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
if proxy_url:
    client.auth._http_client = httpx.Client(proxy=proxy_url)
else:
    client.auth._http_client = httpx.Client(trust_env=True)
