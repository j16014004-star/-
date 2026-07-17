"""Build the job-recommendation and HR-communication Qdrant collections locally."""
from __future__ import annotations

import asyncio

from app.ai.knowledge import (
    ingest_hr_communication_knowledge_to_qdrant,
    ingest_job_recommendation_knowledge_to_qdrant,
)


async def main() -> None:
    job_count = await ingest_job_recommendation_knowledge_to_qdrant()
    hr_count = await ingest_hr_communication_knowledge_to_qdrant()
    print(f"job_recommendation_kb={job_count}")
    print(f"hr_communication_kb={hr_count}")


if __name__ == "__main__":
    asyncio.run(main())
