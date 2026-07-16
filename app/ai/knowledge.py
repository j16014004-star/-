'''Knowledge document loading, chunking, local retrieval and Qdrant integration.'''
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
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
    metadata: dict[str, str | list[str]] = field(default_factory=dict)


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
                    metadata=_infer_metadata(path, section, part),
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
        self.last_results: list[dict] = []

    async def retrieve(
        self, query: str, *, top_k: int | None = None,
        filters: dict[str, str | list[str]] | None = None,
    ) -> list[KnowledgeChunk]:
        limit = max(1, top_k or settings.AI_RAG_TOP_K)
        if settings.QDRANT_ENABLED:
            try:
                candidate_limit = limit * max(1, settings.AI_RAG_CANDIDATE_MULTIPLIER)
                chunks = await self._retrieve_qdrant(query, candidate_limit, filters)
                chunks = _hybrid_rerank(query, chunks)[:limit]
                self.last_source = "qdrant_vector"
                self.last_error = None
                self.last_results = _retrieval_audit(chunks)
                return chunks
            except Exception as exc:
                self.last_source = "local_keyword_fallback"
                self.last_error = f"Qdrant retrieval failed: {type(exc).__name__}"
        else:
            self.last_source = "local_keyword"
            self.last_error = None
        chunks = await asyncio.to_thread(self._retrieve_local, query, limit, filters)
        self.last_results = _retrieval_audit(chunks)
        return chunks

    def _retrieve_local(
        self, query: str, limit: int,
        filters: dict[str, str | list[str]] | None = None,
    ) -> list[KnowledgeChunk]:
        query_terms = _search_terms(query)
        chunks = [
            chunk for chunk in load_knowledge_chunks(self.source_dir)
            if _matches_metadata(chunk.metadata, filters)
        ]
        for chunk in chunks:
            chunk_terms = _search_terms(f'{chunk.title} {chunk.section} {chunk.content}')
            overlap = len(query_terms & chunk_terms)
            coverage = overlap / max(1, len(query_terms))
            chunk.score = coverage + min(overlap, 10) * 0.01
        ranked = sorted(chunks, key=lambda item: item.score, reverse=True)
        positive = [item for item in ranked if item.score > 0]
        return (positive or ranked)[:limit]

    async def _retrieve_qdrant(
        self, query: str, limit: int,
        filters: dict[str, str | list[str]] | None = None,
    ) -> list[KnowledgeChunk]:
        from qdrant_client import models

        vector = await self.gateway.embed_text(query)
        client = _create_qdrant_client()
        try:
            response = await client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=limit,
                query_filter=_qdrant_filter(filters, models),
                with_payload=True,
            )
            chunks: list[KnowledgeChunk] = []
            for point in response.points:
                payload = point.payload or {}
                score = float(point.score or 0)
                if score < settings.AI_RAG_MIN_VECTOR_SCORE:
                    continue
                chunks.append(
                    KnowledgeChunk(
                        id=str(payload.get('chunk_id') or point.id),
                        document_id=str(payload.get('document_id') or ''),
                        title=str(payload.get('title') or ''),
                        section=str(payload.get('section') or ''),
                        content=str(payload.get('content') or ''),
                        source_file=str(payload.get('source_file') or ''),
                        version=str(payload.get('version') or ''),
                        score=score,
                        metadata=dict(payload.get("metadata") or {}),
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


class SkillAssessmentKnowledgeRetriever(BaseKnowledgeRetriever):
    def __init__(self, gateway: TencentMaaSModelGateway | None = None) -> None:
        super().__init__(
            source_dir=settings.SKILL_ASSESSMENT_KB_SOURCE_DIR,
            collection_name=settings.QDRANT_SKILL_ASSESSMENT_COLLECTION,
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


async def ingest_skill_assessment_knowledge_to_qdrant(
    gateway: TencentMaaSModelGateway | None = None,
) -> int:
    return await ingest_knowledge_to_qdrant(
        source_dir=settings.SKILL_ASSESSMENT_KB_SOURCE_DIR,
        processed_dir=settings.SKILL_ASSESSMENT_KB_PROCESSED_DIR,
        collection_name=settings.QDRANT_SKILL_ASSESSMENT_COLLECTION,
        knowledge_base='skill_assessment',
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
    else:
        await client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(filter=models.Filter(must=[
                models.FieldCondition(
                    key="knowledge_base",
                    match=models.MatchValue(value=knowledge_base),
                )
            ])),
            wait=True,
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
                'metadata': chunk.metadata,
                **chunk.metadata,
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


def _infer_metadata(path: Path, section: str, content: str) -> dict[str, str | list[str]]:
    combined = f"{path.stem} {section} {content}".lower()
    skills = [name for name in (
        "python", "fastapi", "pydantic", "sqlalchemy", "mysql", "postgresql",
        "redis", "jwt", "pytest", "alembic", "docker", "linux", "nginx",
        "git", "asyncio", "qdrant",
    ) if name in combined]
    knowledge_type = "guidance"
    if any(word in section for word in ("评分", "Rubric", "验收", "考核")):
        knowledge_type = "rubric"
    elif any(word in section for word in ("错误", "不足", "扣分", "薄弱")):
        knowledge_type = "mistake"
    elif any(word in section for word in ("实践", "项目", "任务")):
        knowledge_type = "practice"
    level = "all"
    if "初级" in combined and "中级" not in combined and "高级" not in combined:
        level = "junior"
    elif "中级" in combined and "高级" not in combined:
        level = "middle"
    elif "高级" in combined and "初级" not in combined and "中级" not in combined:
        level = "senior"
    return {
        "role": "python_backend",
        "knowledge_type": knowledge_type,
        "level": level,
        "skills": skills,
    }


def _matches_metadata(metadata: dict, filters: dict | None) -> bool:
    if not filters:
        return True
    for key, expected in filters.items():
        actual = metadata.get(key)
        expected_values = set(expected if isinstance(expected, list) else [expected])
        actual_values = set(actual if isinstance(actual, list) else [actual])
        if not expected_values & actual_values:
            return False
    return True


def _qdrant_filter(filters: dict | None, models):
    if not filters:
        return None
    conditions = []
    for key, value in filters.items():
        if isinstance(value, list):
            conditions.append(models.FieldCondition(key=key, match=models.MatchAny(any=value)))
        else:
            conditions.append(models.FieldCondition(key=key, match=models.MatchValue(value=value)))
    return models.Filter(must=conditions)


def _hybrid_rerank(query: str, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
    query_terms = _search_terms(query)
    for chunk in chunks:
        chunk_terms = _search_terms(f"{chunk.title} {chunk.section} {chunk.content}")
        lexical = len(query_terms & chunk_terms) / max(1, len(query_terms))
        chunk.score = round(chunk.score * 0.8 + lexical * 0.2, 6)
    return sorted(chunks, key=lambda item: item.score, reverse=True)


def _retrieval_audit(chunks: list[KnowledgeChunk]) -> list[dict]:
    return [
        {"chunk_id": item.id, "document_id": item.document_id, "score": item.score,
         "source_file": item.source_file, "section": item.section, "version": item.version}
        for item in chunks
    ]
