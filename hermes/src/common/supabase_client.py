from supabase import create_client
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

client = create_client(
    supabase_key=os.getenv("SUPABASE_ANON_KEY"),
    supabase_url=os.getenv("SUPABASE_URL"),
)

# Patch auth client to respect no_proxy environment variable
client.auth._http_client = httpx.Client(trust_env=True)
