from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

# Create Gemini client
# NOTE: This MUST use the CS UI proxy to access Google APIs
# Direct HTTPS connections are blocked by CS UI firewall
client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))