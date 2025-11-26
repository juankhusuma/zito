from supabase import create_client
from dotenv import load_dotenv
from src.utils.logger import HermesLogger
import os
import httpx

load_dotenv()

logger = HermesLogger("supabase")

proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
if proxy_url:
    logger.info("Using proxy for Supabase", proxy_url=proxy_url)
    http_client = httpx.Client(proxy=proxy_url, timeout=30.0)
else:
    logger.info("Using direct connection for Supabase")
    http_client = httpx.Client(trust_env=True, timeout=30.0)

# Create client without options parameter (simpler approach)
client = create_client(
    supabase_key=os.getenv("SUPABASE_ANON_KEY"),
    supabase_url=os.getenv("SUPABASE_URL"),
)

# Override the httpx client for PostgREST (table operations) and Auth
client.postgrest.session = http_client
client.auth._http_client = http_client
