"""Redis queue adapter for the isolated execution pipeline.

The worker service is now implemented in runner.py. This file is kept for API compatibility.
"""
from __future__ import annotations

import json
import os
from typing import Any

import redis

QUEUE_KEY = "codesoft:execution-jobs"


def redis_client() -> redis.Redis:
    return redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)


def queue_submission(job: dict[str, Any]) -> None:
    """Push job to Redis for the runner to consume."""
    redis_client().rpush(QUEUE_KEY, json.dumps(job))
