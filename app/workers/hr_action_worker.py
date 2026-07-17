"""Independent worker for a user-approved HR platform action."""
from __future__ import annotations

import asyncio
import sys

from app.core.database import engine
from app.services.hr_service import execute_hr_apply_action
from app.workers.ai_task_worker import configure_event_loop


async def run(action_id: int) -> int:
    try:
        await execute_hr_apply_action(action_id)
    finally:
        await engine.dispose()
    return 0


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("usage: python -m app.workers.hr_action_worker <action_id>")
        return 2
    configure_event_loop()
    return asyncio.run(run(int(sys.argv[1])))


if __name__ == "__main__":
    raise SystemExit(main())
