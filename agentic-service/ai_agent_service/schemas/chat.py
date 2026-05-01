from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=5)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float
    session_id: str


class ChatSessionSummary(BaseModel):
    session_id: str
    name: str
    summary: str
    last_message_at: str


class ChatSessionsResponse(BaseModel):
    sessions: list[ChatSessionSummary]


class ChatMessage(BaseModel):
    role: str
    content: str
    ts: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessage]


class DeleteSessionResponse(BaseModel):
    session_id: str
    deleted: bool
