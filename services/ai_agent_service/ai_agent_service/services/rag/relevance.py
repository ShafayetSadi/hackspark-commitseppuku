from ai_agent_service.core.config import AIAgentSettings
from ai_agent_service.services.knowledge_base import KNOWLEDGE_BASE

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "how",
    "in",
    "is",
    "of",
    "on",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
}

DOMAIN_HINTS = {
    "api",
    "backend",
    "correctness",
    "crud",
    "database",
    "deployment",
    "gateway",
    "inventory",
    "item",
    "items",
    "jwt",
    "latency",
    "login",
    "maintainability",
    "microservice",
    "microservices",
    "pagination",
    "performance",
    "postgres",
    "register",
    "schema",
    "security",
}


def normalize_terms(text: str) -> set[str]:
    return {
        token.strip(".,?!:;()[]{}\"'").lower()
        for token in text.split()
        if token.strip(".,?!:;()[]{}\"'")
    }


def _knowledge_terms() -> set[str]:
    terms = set(DOMAIN_HINTS)
    for document in KNOWLEDGE_BASE:
        terms.update(topic.lower() for topic in document["topics"])
        terms.update(normalize_terms(document["content"]))
    return terms


def is_relevant_query(query: str, settings: AIAgentSettings) -> bool:
    normalized = normalize_terms(query)
    informative_terms = {term for term in normalized if term not in STOP_WORDS}
    if len(informative_terms) < 2:
        return False

    overlap = informative_terms & _knowledge_terms()
    score = len(overlap) / len(informative_terms)
    return bool(overlap) and score >= settings.min_relevance_score
