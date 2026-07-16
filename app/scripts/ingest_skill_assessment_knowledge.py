"""Prepare and upload the technical skill assessment knowledge base."""
import asyncio

from app.ai.knowledge import ingest_skill_assessment_knowledge_to_qdrant
from app.core.config import settings


async def main() -> None:
    count = await ingest_skill_assessment_knowledge_to_qdrant()
    print(f"已写入 Qdrant collection={settings.QDRANT_SKILL_ASSESSMENT_COLLECTION}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
