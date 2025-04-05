from fastapi import FastAPI
from src.consumer.chat_consumer import ChatConsumer
from contextlib import asynccontextmanager
import asyncio
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    task = loop.create_task(ChatConsumer.consume(loop))
    await task
    logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def health_check():
    return {"status": "ok"}

