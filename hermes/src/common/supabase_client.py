from supabase import create_client
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

# Create httpx client that respects no_proxy environment variable
http_client = httpx.Client(trust_env=True)

client = create_client(
    supabase_key=os.getenv("SUPABASE_ANON_KEY"),
    supabase_url=os.getenv("SUPABASE_URL"),
    options={
        "client": http_client
    }
)
