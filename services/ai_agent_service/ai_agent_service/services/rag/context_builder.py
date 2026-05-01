from ai_agent_service.services.rag.retriever import RetrievedDocument


def build_context(documents: list[RetrievedDocument]) -> str:
    if not documents:
        return ""

    sections = [
        f"[{index}] {document.source}: {document.snippet}"
        for index, document in enumerate(documents, start=1)
    ]
    return "\n".join(sections)
