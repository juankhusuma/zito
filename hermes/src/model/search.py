from pydantic import BaseModel

class Questions(BaseModel):
    is_sufficient: bool
    questions: list[str]

class QnA(BaseModel):
    question: str
    answer: str

class QnAList(BaseModel):
    is_sufficient: bool
    answers: list[QnA]

class ChatMessage(BaseModel):
    content: str
    role: str
    timestamp: str

class History(BaseModel):
    messages: list[ChatMessage]
    session_uid: str
    user_uid: str
    access_token: str
    refresh_token: str