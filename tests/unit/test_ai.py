import pytest


@pytest.mark.anyio
async def test_relevant_query(ai_runtime):
    settings = ai_runtime.core_config.get_settings()
    response = await ai_runtime.api_routes.chat(
        ai_runtime.schemas.ChatRequest(
            query="How does JWT auth protect inventory endpoints?",
            top_k=2,
        ),
        settings=settings,
    )

    assert response.model_dump() == {
        "answer": (
            "JWT auth protects downstream services and keeps gateway checks centralized. "
            "Item inventory tracks category, quantity, and availability trends."
        ),
        "sources": [
            "security/auth.md",
            "catalog/items.md",
        ],
        "confidence": 0.75,
    }


@pytest.mark.anyio
async def test_irrelevant_query(ai_runtime):
    settings = ai_runtime.core_config.get_settings()
    response = await ai_runtime.api_routes.chat(
        ai_runtime.schemas.ChatRequest(
            query="What is the weather in Tokyo today?",
            top_k=2,
        ),
        settings=settings,
    )

    assert response.model_dump() == {
        "answer": "The query is outside the supported platform and hackathon knowledge scope.",
        "sources": [],
        "confidence": 0.0,
    }
