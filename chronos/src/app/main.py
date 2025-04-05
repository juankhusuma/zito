from fastapi import FastAPI
from asyncio import get_running_loop
from .router.chat import router as chat_router  # Use relative import
from fastapi.middleware.cors import CORSMiddleware
from ..producer.chat_producer import ChatProducer  # Use relative import
from contextlib import asynccontextmanager
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = get_running_loop()
    task = loop.create_task(ChatProducer.connect(loop))
    await task
    logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/v1", tags=["chat"])

@app.get("/")
def health_check():
    return {"status": "ok"}