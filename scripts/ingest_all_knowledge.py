"""Rebuild every application knowledge collection."""
from __future__ import annotations

import asyncio

from app.ai.knowledge import (
    ingest_career_knowledge_to_qdrant,
    ingest_hr_communication_knowledge_to_qdrant,
    ingest_job_recommendation_knowledge_to_qdrant,
    ingest_resume_knowledge_to_qdrant,
    ingest_skill_assessment_knowledge_to_qdrant,
    ingest_interview_python_knowledge_to_qdrant,
    ingest_interview_secretary_knowledge_to_qdrant,
)


async def main() -> None:
    counts = {
        "resume_optimization": await ingest_resume_knowledge_to_qdrant(),
        "career_planning": await ingest_career_knowledge_to_qdrant(),
        "skill_assessment": await ingest_skill_assessment_knowledge_to_qdrant(),
        "job_recommendation": await ingest_job_recommendation_knowledge_to_qdrant(),
        "hr_communication": await ingest_hr_communication_knowledge_to_qdrant(),
        "interview_python_backend": await ingest_interview_python_knowledge_to_qdrant(),
        "interview_secretary_studies": await ingest_interview_secretary_knowledge_to_qdrant(),
    }
    for name, count in counts.items():
        print(f"{name}: {count} chunks")


if __name__ == "__main__":
    asyncio.run(main())
