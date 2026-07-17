from __future__ import annotations

import asyncio
import os
import sys

import uvicorn


def configure_windows_event_loop() -> None:
    if sys.platform != "win32":
        return

    policy_factory = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
    if policy_factory is not None:
        asyncio.set_event_loop_policy(policy_factory())


if __name__ == "__main__":
    configure_windows_event_loop()
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
        workers=1,
        loop="asyncio",
        proxy_headers=True,
        forwarded_allow_ips=os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1"),
    )
