from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

# Ensure NO_PROXY is set for Google APIs (bypass CS UI proxy)
# This fixes "Network unreachable" errors
os.environ.setdefault('NO_PROXY', '')
os.environ.setdefault('no_proxy', '')

# Add Google domains to NO_PROXY
current_no_proxy = os.environ.get('NO_PROXY', '')
google_domains = 'googleapis.com,*.googleapis.com,generativelanguage.googleapis.com'

if google_domains not in current_no_proxy:
    new_no_proxy = f"{current_no_proxy},{google_domains}" if current_no_proxy else google_domains
    os.environ['NO_PROXY'] = new_no_proxy
    os.environ['no_proxy'] = new_no_proxy

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))