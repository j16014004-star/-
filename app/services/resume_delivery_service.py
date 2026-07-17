"""Build an immutable PDF artifact for a selected resume version."""
from __future__ import annotations

import hashlib
import html
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import async_playwright

from app.core.config import settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ResumeDeliveryArtifact:
    path: str
    file_name: str
    sha256: str
    resume_id: int
    resume_source: str
    resume_optimization_id: int | None


def _safe_title(value: str) -> str:
    normalized = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value.strip())
    return (normalized.strip(" ._") or "resume")[:80]


def _upload_root() -> Path:
    root = Path(settings.UPLOAD_DIR)
    return root if root.is_absolute() else PROJECT_ROOT / root


async def build_resume_delivery_pdf(
    *,
    user_id: int,
    workspace_id: int,
    resume_id: int,
    resume_source: str,
    resume_optimization_id: int | None,
    title: str,
    text: str,
    original_file_path: str | None = None,
    original_file_type: str | None = None,
) -> ResumeDeliveryArtifact:
    """Create/copy the exact selected version as an immutable PDF and hash it."""
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    version_label = (
        f"optimized-{resume_optimization_id}"
        if resume_source == "optimized"
        else f"original-{resume_id}"
    )
    directory = _upload_root() / "hr_delivery" / str(user_id) / str(workspace_id)
    directory.mkdir(parents=True, exist_ok=True)
    file_name = f"{_safe_title(title)}-{version_label}-{content_hash[:12]}.pdf"
    destination = directory / file_name

    source_path = Path(original_file_path) if original_file_path else None
    if source_path is not None and not source_path.is_absolute():
        source_path = PROJECT_ROOT / source_path
    if (
        resume_source == "original"
        and (original_file_type or "").lower() == "pdf"
        and source_path is not None
        and source_path.is_file()
    ):
        if not destination.is_file():
            shutil.copyfile(source_path, destination)
    elif not destination.is_file():
        escaped_title = html.escape(title)
        escaped_text = html.escape(text)
        document = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 16mm 15mm; }}
body {{ font-family: "Microsoft YaHei", "Noto Sans CJK SC", sans-serif; color: #111827; }}
h1 {{ font-size: 20px; margin: 0 0 16px; text-align: center; }}
pre {{ font: 12px/1.65 "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
       white-space: pre-wrap; overflow-wrap: anywhere; margin: 0; }}
</style></head><body><h1>{escaped_title}</h1><pre>{escaped_text}</pre></body></html>"""
        temp_path = destination.with_suffix(".tmp.pdf")
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.set_content(document, wait_until="load")
                await page.pdf(
                    path=str(temp_path),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                await browser.close()
        temp_path.replace(destination)

    file_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
    return ResumeDeliveryArtifact(
        path=str(destination.resolve()),
        file_name=file_name,
        sha256=file_hash,
        resume_id=resume_id,
        resume_source=resume_source,
        resume_optimization_id=resume_optimization_id,
    )
