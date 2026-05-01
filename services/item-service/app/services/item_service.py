from app.core.config import ItemSettings
from app.models.item import Item
from app.schemas.item import ItemCreateRequest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_item(session: AsyncSession, payload: ItemCreateRequest) -> Item:
    item = Item(name=payload.name, category=payload.category, quantity=payload.quantity)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def list_items(
    session: AsyncSession,
    settings: ItemSettings,
    page: int,
    page_size: int,
    category: str | None,
    search: str | None,
) -> dict:
    clamped_size = min(page_size, settings.max_page_size)
    conditions = []

    if category:
        conditions.append(Item.category == category)
    if search:
        conditions.append(Item.name.ilike(f"%{search}%"))

    count_query = select(func.count(Item.id))
    data_query = select(Item).order_by(Item.created_at.desc())

    for condition in conditions:
        count_query = count_query.where(condition)
        data_query = data_query.where(condition)

    total = await session.scalar(count_query) or 0
    rows = await session.scalars(data_query.offset((page - 1) * clamped_size).limit(clamped_size))
    return {"items": rows.all(), "page": page, "page_size": clamped_size, "total": total}
