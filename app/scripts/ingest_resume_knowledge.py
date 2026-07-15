'''Prepare resume knowledge chunks and optionally upload them to Qdrant.'''
from __future__ import annotations

import argparse
import asyncio

from app.ai.knowledge import (
    ingest_resume_knowledge_to_qdrant,
    load_knowledge_chunks,
    write_processed_chunks,
)
from app.core.config import settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='处理简历优化知识库')
    parser.add_argument(
        '--qdrant',
        action='store_true',
        help='生成向量并写入 Qdrant；不传时只生成本地 chunks.jsonl',
    )
    return parser.parse_args()


async def async_main(upload_qdrant: bool) -> int:
    if upload_qdrant:
        if not settings.QDRANT_ENABLED:
            print('QDRANT_ENABLED=false，未执行云端向量化和 Qdrant 写入')
            return 2
        count = await ingest_resume_knowledge_to_qdrant()
        print(f'已写入 Qdrant，知识块数量: {count}')
        return 0

    chunks = load_knowledge_chunks(settings.RESUME_OPTIMIZATION_KB_SOURCE_DIR)
    target = write_processed_chunks(chunks, settings.RESUME_OPTIMIZATION_KB_PROCESSED_DIR)
    print(f'本地知识库处理完成，知识块数量: {len(chunks)}，输出: {target}')
    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(async_main(args.qdrant))


if __name__ == '__main__':
    raise SystemExit(main())

