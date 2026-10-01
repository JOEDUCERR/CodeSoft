"""Redis queue adapter for the future isolated execution service.

This process never executes submitted source code. A sandbox runner can consume
`codesoft:execution-jobs` and update the submission after execution.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

import redis

QUEUE_KEY = "codesoft:execution-jobs"


def redis_client() -> redis.Redis:
    return redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)


def queue_submission(job: dict[str, Any]) -> None:
    redis_client().rpush(QUEUE_KEY, json.dumps(job))


def worker_loop() -> None:
    """Health-check Redis while jobs remain durable for the sandbox runner."""
    client = redis_client()
    while True:
        client.ping()
        time.sleep(5)


if __name__ == "__main__":
    worker_loop()
