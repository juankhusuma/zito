from fastapi import APIRouter
from ..producer.chat_producer import ChatProducer, History

router = APIRouter()

@router.post("/chat")
async def chat_producer(message: History):
    status = await ChatProducer.publish(message)
    return status