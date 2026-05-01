"""Unit tests for RAG retrieval and mock LLM — no MongoDB, no real LLM needed."""
# ruff: noqa: E402

import sys
from pathlib import Path

import pytest

AGENTIC = Path(__file__).parents[2] / "agentic-service"
if str(AGENTIC) not in sys.path:
    sys.path.insert(0, str(AGENTIC))

from ai_agent_service.core.config import AIAgentSettings
from ai_agent_service.services.llm.mock_llm import MockLLM
from ai_agent_service.services.rag.context_builder import build_context
from ai_agent_service.services.rag.relevance import is_relevant_query
from ai_agent_service.services.rag.retriever import retrieve_documents


@pytest.fixture
def settings():
    return AIAgentSettings(app_env="dev", jwt_secret="test", min_relevance_score=0.2)


@pytest.mark.asyncio
async def test_relevant_query_returns_answer(settings):
    llm = MockLLM()
    query = "How does JWT auth protect inventory endpoints?"
    assert is_relevant_query(query, settings)
    docs = retrieve_documents(query, top_k=3)
    context = build_context(docs)
    answer, sources, confidence = await llm.generate_answer(query, docs, context)
    assert answer
    assert len(sources) > 0
    assert confidence > 0


@pytest.mark.asyncio
async def test_irrelevant_query_filtered(settings):
    query = "What is the weather in Tokyo today?"
    assert not is_relevant_query(query, settings)


@pytest.mark.asyncio
async def test_mock_llm_no_docs(settings):
    llm = MockLLM()
    answer, sources, confidence = await llm.generate_answer("query", [], "", None)
    assert "Insufficient" in answer
    assert sources == []
    assert confidence < 0.2
