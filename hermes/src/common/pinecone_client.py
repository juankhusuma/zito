from pinecone import Pinecone
from dotenv import load_dotenv
from src.utils.logger import HermesLogger
import os
load_dotenv()

logger = HermesLogger("pinecone")

proxy_url = os.getenv("PINECONE_PROXY_URL") or os.getenv("HTTPS_PROXY")

if proxy_url:
    logger.info("Using proxy for Pinecone", proxy_url=proxy_url)

# Initialize Pinecone clients
_pc = None
_pc_2 = None
_kuhp_index = None
_kuhper_index = None
_undang_undang_index = None
_perpres_index = None

def get_pc():
    global _pc
    if _pc is None:
        _pc = Pinecone(
            api_key=os.getenv("PINECONE_API_KEY"),
            proxy_url=proxy_url
        )
    return _pc

def get_pc_2():
    global _pc_2
    if _pc_2 is None:
        _pc_2 = Pinecone(
            api_key=os.getenv("PINECONE_API_KEY_2"),
            proxy_url=proxy_url
        )
    return _pc_2

def get_kuhp_index():
    global _kuhp_index
    if _kuhp_index is None:
        _kuhp_index = get_pc().Index("kuhp-demo-gemini")
    return _kuhp_index

def get_kuhper_index():
    global _kuhper_index
    if _kuhper_index is None:
        _kuhper_index = get_pc_2().Index("kuhper")
    return _kuhper_index

def get_undang_undang_index():
    global _undang_undang_index
    if _undang_undang_index is None:
        _undang_undang_index = get_pc_2().Index("undang-undang")
    return _undang_undang_index

def get_perpres_index():
    global _perpres_index
    if _perpres_index is None:
        _perpres_index = get_pc_2().Index("perpres")
    return _perpres_index

class _LazyIndex:
    def __init__(self, getter_func):
        self._getter = getter_func
        self._index = None

    def __getattr__(self, name):
        if self._index is None:
            self._index = self._getter()
        return getattr(self._index, name)

kuhp_index = _LazyIndex(get_kuhp_index)
kuhper_index = _LazyIndex(get_kuhper_index)
undang_undang_index = _LazyIndex(get_undang_undang_index)
perpres_index = _LazyIndex(get_perpres_index)