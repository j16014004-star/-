'''Knowledge document loading, chunking, local retrieval and Qdrant integration.'''
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.ai.tencent_maas import TencentMaaSModelGateway
from app.core.config import settings


SUPPORTED_EXTENSIONS = {'.md', '.txt', '.docx', '.pdf'}


@dataclass(slots=True)
class KnowledgeChunk:
    id: str
    document_id: str
    title: str
    section: str
    content: str
    source_file: str
    version: str
    score: float = 0.0


def normalize_text(text: str) -> str:
    text = text.replace('\x00', '')
    text = re.sub(r'\r\n?', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def read_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {'.md', '.txt'}:
        return normalize_text(path.read_text(encoding='utf-8'))
    if suffix == '.docx':
        from docx import Document

        document = Document(path)
        return normalize_text('\n\n'.join(p.text for p in document.paragraphs if p.text.strip()))
    if suffix == '.pdf':
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            return normalize_text('\n\n'.join((page.extract_text() or '') for page in pdf.pages))
    raise ValueError(f'不支持的知识文档格式: {suffix}')


def split_document(path: Path, *, chunk_size: int, overlap: int) -> list[KnowledgeChunk]:
    text = read_document(path)
    if not text:
        return []
    version = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    document_id = hashlib.sha256(path.name.encode('utf-8')).hexdigest()[:20]
    title = path.stem
    sections = _markdown_sections(text, default_title=title)
    chunks: list[KnowledgeChunk] = []
    for section, content in sections:
        for part_index, part in enumerate(_sliding_chunks(content, chunk_size, overlap)):
            raw_id = f'{document_id}:{version}:{section}:{part_index}'
            chunk_id = hashlib.sha256(raw_id.encode('utf-8')).hexdigest()
            chunks.append(
                KnowledgeChunk(
                    id=chunk_id,
                    document_id=document_id,
                    title=title,
                    section=section,
                    content=part,
                    source_file=path.name,
                    version=version,
                )
            )
    return chunks


def load_knowledge_chunks(source_dir: str | Path) -> list[KnowledgeChunk]:
    root = Path(source_dir).resolve()
    if not root.exists():
        return []
    chunks: list[KnowledgeChunk] = []
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            chunks.extend(
                split_document(
                    path,
                    chunk_size=settings.AI_RAG_CHUNK_SIZE,
                    overlap=settings.AI_RAG_CHUNK_OVERLAP,
                )
            )
    return chunks


def write_processed_chunks(chunks: list[KnowledgeChunk], processed_dir: str | Path) -> Path:
    target_dir = Path(processed_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / 'chunks.jsonl'
    with target.open('w', encoding='utf-8', newline='\n') as file:
        for chunk in chunks:
            file.write(json.dumps(asdict(chunk), ensure_ascii=False) + '\n')
    return target


class BaseKnowledgeRetriever:
    def __init__(
        self,
        *,
        source_dir: str | Path,
        collection_name: str,
        gateway: TencentMaaSModelGateway | None = None,
    ) -> None:
        self.source_dir = source_dir
        self.collection_name = collection_name
        self.gateway = gateway or TencentMaaSModelGateway()
        self.last_source = "not_run"
        self.last_error: str | None = None

    async def retrieve(self, query: str, *, top_k: int | None = None) -> list[KnowledgeChunk]:
        limit = max(1, top_k or settings.AI_RAG_TOP_K)
        if settings.QDRANT_ENABLED:
            try:
                chunks = await self._retrieve_qdrant(query, limit)
                self.last_source = "qdrant_vector"
                self.last_error = None
                return chunks
            except Exception as exc:
                self.last_source = "local_keyword_fallback"
                self.last_error = f"Qdrant retrieval failed: {type(exc).__name__}"
        else:
            self.last_source = "local_keyword"
            self.last_error = None
        return await asyncio.to_thread(self._retrieve_local, query, limit)

    def _retrieve_local(self, query: str, limit: int) -> list[KnowledgeChunk]:
        query_terms = _search_terms(query)
        chunks = load_knowledge_chunks(self.source_dir)
        for chunk in chunks:
            chunk_terms = _search_terms(f'{chunk.title} {chunk.section} {chunk.content}')
            overlap = len(query_terms & chunk_terms)
            coverage = overlap / max(1, len(query_terms))
            chunk.score = coverage + min(overlap, 10) * 0.01
        ranked = sorted(chunks, key=lambda item: item.score, reverse=True)
        positive = [item for item in ranked if item.score > 0]
        return (positive or ranked)[:limit]

    async def _retrieve_qdrant(self, query: str, limit: int) -> list[KnowledgeChunk]:
        vector = await self.gateway.embed_text(query)
        client = _create_qdrant_client()
        try:
            response = await client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=limit,
                with_payload=True,
            )
            chunks: list[KnowledgeChunk] = []
            for point in response.points:
                payload = point.payload or {}
                chunks.append(
                    KnowledgeChunk(
                        id=str(payload.get('chunk_id') or point.id),
                        document_id=str(payload.get('document_id') or ''),
                        title=str(payload.get('title') or ''),
                        section=str(payload.get('section') or ''),
                        content=str(payload.get('content') or ''),
                        source_file=str(payload.get('source_file') or ''),
                        version=str(payload.get('version') or ''),
                        score=float(point.score or 0),
                    )
                )
            return chunks
        finally:
            await client.close()


class ResumeKnowledgeRetriever(BaseKnowledgeRetriever):
    def __init__(self, gateway: TencentMaaSModelGateway | None = None) -> None:
        super().__init__(
            source_dir=settings.RESUME_OPTIMIZATION_KB_SOURCE_DIR,
            collection_name=settings.QDRANT_RESUME_COLLECTION,
            gateway=gateway,
        )


class CareerKnowledgeRetriever(BaseKnowledgeRetriever):
    def __init__(self, gateway: TencentMaaSModelGateway | None = None) -> None:
        super().__init__(
            source_dir=settings.CAREER_PLANNING_KB_SOURCE_DIR,
            collection_name=settings.QDRANT_CAREER_COLLECTION,
            gateway=gateway,
        )


async def ingest_resume_knowledge_to_qdrant(
    gateway: TencentMaaSModelGateway | None = None,
) -> int:
    return await ingest_knowledge_to_qdrant(
        source_dir=settings.RESUME_OPTIMIZATION_KB_SOURCE_DIR,
        processed_dir=settings.RESUME_OPTIMIZATION_KB_PROCESSED_DIR,
        collection_name=settings.QDRANT_RESUME_COLLECTION,
        knowledge_base='resume_optimization',
        gateway=gateway,
    )


async def ingest_career_knowledge_to_qdrant(
    gateway: TencentMaaSModelGateway | None = None,
) -> int:
    return await ingest_knowledge_to_qdrant(
        source_dir=settings.CAREER_PLANNING_KB_SOURCE_DIR,
        processed_dir=settings.CAREER_PLANNING_KB_PROCESSED_DIR,
        collection_name=settings.QDRANT_CAREER_COLLECTION,
        knowledge_base='career_planning',
        gateway=gateway,
    )


async def ingest_knowledge_to_qdrant(
    *,
    source_dir: str | Path,
    processed_dir: str | Path,
    collection_name: str,
    knowledge_base: str,
    gateway: TencentMaaSModelGateway | None = None,
) -> int:
    from qdrant_client import models

    model_gateway = gateway or TencentMaaSModelGateway()
    chunks = load_knowledge_chunks(source_dir)
    write_processed_chunks(chunks, processed_dir)
    if not settings.QDRANT_ENABLED:
        return len(chunks)
    client = _create_qdrant_client()
    if not await client.collection_exists(collection_name):
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=settings.TENCENT_MAAS_EMBEDDING_DIMENSION,
                distance=models.Distance.COSINE,
            ),
        )
    for chunk in chunks:
        vector = await model_gateway.embed_text(chunk.content)
        point = models.PointStruct(
            id=str(uuid5(NAMESPACE_URL, chunk.id)),
            vector=vector,
            payload={
                'chunk_id': chunk.id,
                'document_id': chunk.document_id,
                'title': chunk.title,
                'section': chunk.section,
                'content': chunk.content,
                'source_file': chunk.source_file,
                'version': chunk.version,
                'knowledge_base': knowledge_base,
                'status': 'active',
            },
        )
        await client.upsert(
            collection_name=collection_name,
            points=[point],
            wait=True,
        )
    await client.close()
    return len(chunks)


def prepare_career_knowledge_chunks() -> int:
    chunks = load_knowledge_chunks(settings.CAREER_PLANNING_KB_SOURCE_DIR)
    write_processed_chunks(chunks, settings.CAREER_PLANNING_KB_PROCESSED_DIR)
    return len(chunks)


def _create_qdrant_client():
    from qdrant_client import AsyncQdrantClient

    if settings.QDRANT_LOCAL_MODE:
        path = Path(settings.QDRANT_LOCAL_PATH).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return AsyncQdrantClient(path=str(path))
    return AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY or None,
        timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
    )


def _markdown_sections(text: str, *, default_title: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title = default_title
    buffer: list[str] = []
    for line in text.splitlines():
        match = re.match(r'^#{1,6}\s+(.+)$', line.strip())
        if match:
            if buffer and normalize_text('\n'.join(buffer)):
                sections.append((current_title, normalize_text('\n'.join(buffer))))
            current_title = match.group(1).strip()
            buffer = []
        else:
            buffer.append(line)
    if buffer and normalize_text('\n'.join(buffer)):
        sections.append((current_title, normalize_text('\n'.join(buffer))))
    return sections or [(default_title, text)]


def _sliding_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    safe_size = max(200, chunk_size)
    safe_overlap = max(0, min(overlap, safe_size // 2))
    paragraphs = [part.strip() for part in re.split(r'\n\s*\n', text) if part.strip()]
    chunks: list[str] = []
    current = ''
    for paragraph in paragraphs:
        candidate = f'{current}\n\n{paragraph}'.strip() if current else paragraph
        if len(candidate) <= safe_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= safe_size:
            current = paragraph
            continue
        start = 0
        step = safe_size - safe_overlap
        while start < len(paragraph):
            chunks.append(paragraph[start:start + safe_size])
            start += step
        current = ''
    if current:
        chunks.append(current)
    return chunks


def _search_terms(text: str) -> set[str]:
    lowered = text.lower()
    latin = set(re.findall(r'[a-z0-9+#.]{2,}', lowered))
    chinese = ''.join(re.findall(r'[\u4e00-\u9fff]', lowered))
    bigrams = {chinese[index:index + 2] for index in range(max(0, len(chinese) - 1))}
    return latin | bigrams
