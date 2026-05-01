from dataclasses import dataclass

from ai_agent_service.services.knowledge_base import KNOWLEDGE_BASE
from ai_agent_service.services.rag.relevance import normalize_terms


@dataclass(frozen=True)
class RetrievedDocument:
    source: str
    snippet: str
    score: float


def _score_document(query_terms: set[str], document: dict) -> float:
    topic_terms = {topic.lower() for topic in document["topics"]}
    content_terms = normalize_terms(document["content"])
    document_terms = topic_terms | content_terms
    if not query_terms or not document_terms:
        return 0.0
    overlap = query_terms & document_terms
    return len(overlap) / len(document_terms)


def retrieve_documents(query: str, top_k: int) -> list[RetrievedDocument]:
    query_terms = normalize_terms(query)
    ranked = sorted(
        (
            RetrievedDocument(
                source=document["source"],
                snippet=document["content"],
                score=_score_document(query_terms, document),
            )
            for document in KNOWLEDGE_BASE
        ),
        key=lambda document: (-document.score, document.source),
    )
    return [document for document in ranked[:top_k] if document.score > 0]
