"""Background monitor for one full-auto HR workspace."""
from __future__ import annotations

import asyncio
import os
import sys
from time import monotonic

from app.core.database import engine
from app.services.hr_service import run_workspace_monitor_cycle
from app.workers.ai_task_worker import configure_event_loop


def interval_seconds() -> int:
    try:
        return max(15, int(os.getenv("HR_MONITOR_INTERVAL_SECONDS", "30")))
    except ValueError:
        return 30


def max_runtime_seconds() -> int:
    try:
        return max(300, int(os.getenv("HR_MONITOR_MAX_SECONDS", "43200")))
    except ValueError:
        return 43200


async def run(workspace_id: int) -> int:
    started = monotonic()
    consecutive_errors = 0
    try:
        while monotonic() - started < max_runtime_seconds():
            try:
                if not await run_workspace_monitor_cycle(workspace_id):
                    return 0
                consecutive_errors = 0
            except Exception as exc:
                consecutive_errors += 1
                print(f"HR monitor cycle failed ({consecutive_errors}/3): {exc}")
                if consecutive_errors >= 3:
                    return 1
            await asyncio.sleep(interval_seconds())
    finally:
        await engine.dispose()
    return 0


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("usage: python -m app.workers.hr_monitor_worker <workspace_id>")
        return 2
    configure_event_loop()
    return asyncio.run(run(int(sys.argv[1])))


if __name__ == "__main__":
    raise SystemExit(main())
