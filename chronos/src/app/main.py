from fastapi import FastAPI, APIRouter
from asyncio import get_running_loop
from ..router.chat import router as chat_router
from ..router.search import router as search_router
from fastapi.middleware.cors import CORSMiddleware
from ..producer.chat_producer import ChatProducer
from contextlib import asynccontextmanager
import logging
import asyncio

router = APIRouter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )

    loop = get_running_loop()
    task = loop.create_task(ChatProducer.connect(loop))
    logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    yield
    # Clean up the task when shutting down
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router, tags=["chat"], prefix="/api/v1")
app.include_router(search_router, tags=["search"], prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "ok"}