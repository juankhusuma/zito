from fastapi import FastAPI
from src.consumer.chat_consumer import ChatConsumer
from src.utils.logger import setup_logging
from contextlib import asynccontextmanager
import asyncio
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
    loop = asyncio.get_running_loop()
    task = loop.create_task(ChatConsumer.consume(loop))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

@app.get("/")
def health_check():
    return {"status": "ok"}