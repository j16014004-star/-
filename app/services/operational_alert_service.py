"""Process-safe JSONL operational alerts for worker failures."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def emit_operational_alert(
    *,
    category: str,
    message: str,
    severity: str = "error",
    context: dict | None = None,
) -> None:
    log_path = Path(settings.OPERATIONS_ALERT_LOG)
    if not log_path.is_absolute():
        log_path = PROJECT_ROOT / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "category": category[:100],
        "message": message[:1000],
        "context": context or {},
    }
    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    try:
        os.chmod(log_path, 0o600)
    except OSError:
        pass
