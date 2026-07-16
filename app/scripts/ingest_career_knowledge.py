"""Prepare career planning knowledge chunks and optionally upload them to Qdrant."""
from __future__ import annotations

import asyncio

from app.ai.knowledge import ingest_career_knowledge_to_qdrant, load_knowledge_chunks, write_processed_chunks
from app.core.config import settings


async def main() -> None:
    chunks = load_knowledge_chunks(settings.CAREER_PLANNING_KB_SOURCE_DIR)
    target = write_processed_chunks(chunks, settings.CAREER_PLANNING_KB_PROCESSED_DIR)
    print(f"已生成职业规划知识库切片: {len(chunks)} -> {target}")
    if settings.QDRANT_ENABLED:
        count = await ingest_career_knowledge_to_qdrant()
        print(f"已写入 Qdrant collection={settings.QDRANT_CAREER_COLLECTION}: {count}")
    else:
        print("QDRANT_ENABLED=false，未执行云端向量化和 Qdrant 写入")


if __name__ == "__main__":
    asyncio.run(main())
