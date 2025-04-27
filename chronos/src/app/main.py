from fastapi import FastAPI, APIRouter
from asyncio import get_running_loop
from ..router.chat import router as chat_router  # Use relative import
from fastapi.middleware.cors import CORSMiddleware
from ..producer.chat_producer import ChatProducer  # Use relative import
from contextlib import asynccontextmanager
# from fastapi_utilities import repeat_every
import logging

router = APIRouter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = get_running_loop()
    task = loop.create_task(ChatProducer.connect(loop))
    await task
    logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    
    # Setup periodic task with repeat_every
    # @repeat_every(seconds=3)
    # async def print_hello():
    #     print("hello")
    
    # task = loop.create_task(print_hello())
    
    yield
    # if not task.done():
    #     task.cancel()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router, tags=["chat"], prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "ok"}