from app.core.config import ItemSettings, get_settings
from app.db.session import get_db_session
from app.schemas.item import ItemCreateRequest, ItemResponse, PaginatedItemsResponse
from app.services.item_service import create_item, list_items
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok", "service": "item-service"}


@router.get("/items", response_model=PaginatedItemsResponse)
async def get_items(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    search: str | None = None,
    session: AsyncSession = Depends(get_db_session),
    settings: ItemSettings = Depends(get_settings),
) -> PaginatedItemsResponse:
    result = await list_items(session, settings, page, page_size, category, search)
    return PaginatedItemsResponse(
        items=[ItemResponse.from_model(item) for item in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def post_item(
    payload: ItemCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ItemResponse:
    item = await create_item(session, payload)
    return ItemResponse.from_model(item)
