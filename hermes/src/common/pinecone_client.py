from pinecone import Pinecone
from dotenv import load_dotenv
import os
load_dotenv()

pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY"),
    # proxy_url="http://proxy.cs.ui.ac.id:8080"    
)
pc_2 = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY_2"),
    # proxy_url="http://proxy.cs.ui.ac.id:8080"    
)
# index = pc.Index("lexin")
index_list = pc.list_indexes()
print(index_list)

kuhp_index = pc.Index("kuhp-demo-gemini")
index_list_2 = pc_2.list_indexes()
print(index_list_2)
kuhper_index = pc_2.Index("kuhper")
undang_undang_index = pc_2.Index("undang-undang")