from datetime import datetime

from pydantic import BaseModel, Field


class ItemCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=100)
    quantity: int = Field(ge=0, le=1_000_000)


class ItemResponse(BaseModel):
    id: int
    name: str
    category: str
    quantity: int
    created_at: datetime

    @classmethod
    def from_model(cls, item) -> "ItemResponse":
        return cls(
            id=item.id,
            name=item.name,
            category=item.category,
            quantity=item.quantity,
            created_at=item.created_at,
        )


class PaginatedItemsResponse(BaseModel):
    items: list[ItemResponse]
    page: int
    page_size: int
    total: int
