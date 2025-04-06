from ollama import Client
from dotenv import load_dotenv
import os
load_dotenv()

infer = Client(
    host=os.getenv("OLLAMA_URL", "http://localhost:11434"),
)