from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

client = create_client(
    supabase_key=os.getenv("SUPABASE_ANON_KEY"),
    supabase_url=os.getenv("SUPABASE_URL"),
)
