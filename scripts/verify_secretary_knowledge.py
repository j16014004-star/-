"""Verify that every runtime retriever returns secretary-domain knowledge."""
from __future__ import annotations

import asyncio

from app.ai.knowledge import (
    CareerKnowledgeRetriever,
    HrCommunicationKnowledgeRetriever,
    JobRecommendationKnowledgeRetriever,
    ResumeKnowledgeRetriever,
    SkillAssessmentKnowledgeRetriever,
)


async def main() -> None:
    retriever_types = (
        ResumeKnowledgeRetriever,
        CareerKnowledgeRetriever,
        SkillAssessmentKnowledgeRetriever,
        JobRecommendationKnowledgeRetriever,
        HrCommunicationKnowledgeRetriever,
    )
    for retriever_type in retriever_types:
        retriever = retriever_type()
        chunks = await retriever.retrieve(
            "秘书学 行政助理 公文写作 会议纪要 档案管理",
            top_k=2,
            filters={"role": ["secretary_studies", "general"]},
        )
        roles = [chunk.metadata.get("role") for chunk in chunks]
        if not chunks or "secretary_studies" not in roles or "python_backend" in roles:
            raise RuntimeError(f"{retriever_type.__name__} 专业隔离校验失败: {roles}")
        print(
            f"{retriever_type.__name__}: source={retriever.last_source}, "
            f"roles={roles}, titles={[chunk.title for chunk in chunks]}"
        )


if __name__ == "__main__":
    asyncio.run(main())
