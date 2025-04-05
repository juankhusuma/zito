from supabase import create_async_client
from dotenv import load_dotenv
import os

load_dotenv()

client = create_async_client(
    supabase_key=os.getenv("SUPABASE_ANON_KEY"),
    supabase_url=os.getenv("SUPABASE_URL"),
)

supabase_client = client
initialized = False
async def get_client():
    global supabase_client, initialized
    if not initialized:
        supabase_client = await client
        initialized = True
    return supabase_client