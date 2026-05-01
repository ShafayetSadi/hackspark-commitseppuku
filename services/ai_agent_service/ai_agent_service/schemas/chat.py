from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(min_length=5, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=5)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float
