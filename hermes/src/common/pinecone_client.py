from pinecone import Pinecone
from dotenv import load_dotenv
import os
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
# index = pc.Index("lexin")
index_list = pc.list_indexes()
print(index_list)

kuhp_index = pc.Index("kuhp-demo-gemini")