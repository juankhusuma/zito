from supabase import create_client
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

# Configure httpx client with proxy and timeout for ALL Supabase operations
proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
if proxy_url:
    print(f"INFO: Using proxy for Supabase: {proxy_url}")
    http_client = httpx.Client(proxy=proxy_url, timeout=30.0)
else:
    print("INFO: Using direct connection for Supabase (trust_env)")
    http_client = httpx.Client(trust_env=True, timeout=30.0)

# Create client without options parameter (simpler approach)
client = create_client(
    supabase_key=os.getenv("SUPABASE_ANON_KEY"),
    supabase_url=os.getenv("SUPABASE_URL"),
)

# Override the httpx client for PostgREST (table operations) and Auth
client.postgrest.session = http_client
client.auth._http_client = http_client
