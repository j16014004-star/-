import hashlib
import json
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from playwright.async_api import async_playwright

from app.automations.job_58_apply import upload_selected_resume
from app.core.config import settings
from app.services.platform_session_service import (
    encrypt_storage_state_file,
    is_plausible_storage_state,
    load_storage_state,
)
from app.services.operational_alert_service import emit_operational_alert
from app.services.resume_delivery_service import build_resume_delivery_pdf


@pytest.mark.asyncio
async def test_optimized_resume_is_rendered_to_hashed_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    artifact = await build_resume_delivery_pdf(
        user_id=7,
        workspace_id=11,
        resume_id=3,
        resume_source="optimized",
        resume_optimization_id=19,
        title="Python后端工程师简历",
        text="姓名：测试用户\n项目经验：FastAPI 招聘系统",
    )

    output = Path(artifact.path)
    assert output.is_file()
    assert output.read_bytes().startswith(b"%PDF")
    assert artifact.file_name.endswith(".pdf")
    assert artifact.resume_optimization_id == 19
    assert artifact.sha256 == hashlib.sha256(output.read_bytes()).hexdigest()


@pytest.mark.asyncio
async def test_original_pdf_is_copied_as_exact_version(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF-1.4\nselected-original-version")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

    artifact = await build_resume_delivery_pdf(
        user_id=8,
        workspace_id=12,
        resume_id=4,
        resume_source="original",
        resume_optimization_id=None,
        title="原始简历",
        text="原始简历文本",
        original_file_path=str(source),
        original_file_type="pdf",
    )

    assert Path(artifact.path).read_bytes() == source.read_bytes()
    assert artifact.resume_source == "original"


@pytest.mark.asyncio
async def test_file_input_receives_exact_selected_pdf(tmp_path):
    resume_file = tmp_path / "selected-resume.pdf"
    resume_file.write_bytes(b"%PDF-1.4\nselected")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content("<input type='file' accept='.pdf'>")
            strategy = await upload_selected_resume(page, str(resume_file))
            selected_name = await page.locator("input[type=file]").evaluate(
                "(element) => element.files[0].name"
            )
        finally:
            await browser.close()

    assert strategy == "direct_file_input"
    assert selected_name == resume_file.name


def test_platform_storage_state_is_encrypted_at_rest(tmp_path, monkeypatch):
    monkeypatch.setattr(
        settings,
        "PLATFORM_STATE_ENCRYPTION_KEY",
        Fernet.generate_key().decode("ascii"),
    )
    plain = tmp_path / "58.json.tmp"
    encrypted = tmp_path / "58.enc"
    plain.write_text(
        '{"cookies":[{"name":"id58","value":"secret-cookie",'
        '"domain":".58.com","expires":-1}],"origins":[]}',
        encoding="utf-8",
    )

    encrypt_storage_state_file(plain, encrypted)

    assert not plain.exists()
    assert encrypted.is_file()
    assert b"secret-cookie" not in encrypted.read_bytes()
    assert load_storage_state(encrypted)["cookies"][0]["value"] == "secret-cookie"
    assert is_plausible_storage_state(encrypted, "58") is True


def test_invalid_storage_state_is_removed_automatically(tmp_path):
    invalid = tmp_path / "58.enc"
    invalid.write_bytes(b"invalid-encrypted-state")

    assert is_plausible_storage_state(invalid, "58") is False
    assert not invalid.exists()


def test_operational_alert_is_written_as_structured_json(tmp_path, monkeypatch):
    alert_log = tmp_path / "alerts" / "operations.jsonl"
    monkeypatch.setattr(settings, "OPERATIONS_ALERT_LOG", str(alert_log))

    emit_operational_alert(
        category="worker_failed",
        message="测试失败",
        context={"task_id": "task-1"},
    )

    payload = json.loads(alert_log.read_text(encoding="utf-8").strip())
    assert payload["category"] == "worker_failed"
    assert payload["message"] == "测试失败"
    assert payload["context"]["task_id"] == "task-1"
