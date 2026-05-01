import pytest
from conftest import AsyncSessionAdapter


@pytest.mark.anyio
async def test_create_item(item_runtime):
    with item_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        response = await item_runtime.api_routes.post_item(
            item_runtime.schemas.ItemCreateRequest(
                name="Camera",
                category="rental",
                quantity=3,
            ),
            session=session,
        )

    payload = response.model_dump()
    assert payload["name"] == "Camera"
    assert payload["category"] == "rental"
    assert payload["quantity"] == 3
    assert payload["id"] == 1


@pytest.mark.anyio
async def test_list_items_with_pagination(item_runtime):
    settings = item_runtime.core_config.get_settings()

    with item_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        for index in range(3):
            await item_runtime.api_routes.post_item(
                item_runtime.schemas.ItemCreateRequest(
                    name=f"Camera {index}",
                    category="rental",
                    quantity=index + 1,
                ),
                session=session,
            )

    with item_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        response = await item_runtime.api_routes.get_items(
            page=1,
            page_size=2,
            category="rental",
            search="Camera",
            session=session,
            settings=settings,
        )

    payload = response.model_dump()
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert payload["total"] == 3
    assert len(payload["items"]) == 2


@pytest.mark.anyio
async def test_list_items_out_of_bounds_page(item_runtime):
    settings = item_runtime.core_config.get_settings()

    with item_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        for i in range(2):
            await item_runtime.api_routes.post_item(
                item_runtime.schemas.ItemCreateRequest(
                    name=f"Item {i}",
                    category="test",
                    quantity=1,
                ),
                session=session,
            )

    with item_runtime.session_factory() as sync_session:
        session = AsyncSessionAdapter(sync_session)
        response = await item_runtime.api_routes.get_items(
            page=99,
            page_size=20,
            category=None,
            search=None,
            session=session,
            settings=settings,
        )

    payload = response.model_dump()
    assert payload["total"] == 2
    assert payload["items"] == []
    assert payload["page"] == 99
