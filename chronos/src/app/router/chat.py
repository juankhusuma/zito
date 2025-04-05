from fastapi import APIRouter, Depends
from src.producer.chat_producer import ChatProducer, History
from typing import Annotated

router = APIRouter()

@router.post("/chat")
async def chat_producer(message: History, status: Annotated[dict, Depends(ChatProducer.publish)]):
    return status