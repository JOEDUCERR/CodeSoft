from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from collections import deque
from typing import Any

from database import fetch_problem_by_id_or_slug

try:
    import redis
except ImportError:  # pragma: no cover - optional dependency for production infra
    redis = None


JOB_QUEUE_KEY = "codesoft:jobs"
_MEMORY_QUEUE: deque[dict[str, Any]] = deque()
_MEMORY_LOCK = threading.Lock()
_WORKER_THREAD: threading.Thread | None = None
_WORKER_STOP = threading.Event()


def normalize_code(code: str) -> str:
    return re.sub(r"\s+", " ", code or "").strip()


def looks_empty(code: str) -> bool:
    normalized = normalize_code(code)
    if len(normalized) < 24:
        return True
    stripped = normalized
    for needle in [
        "from typing import",
        "#include",
        "using namespace std;",
        "import java.util.*;",
        "class Solution",
        "public:",
        "pass",
        "return -1;",
    ]:
        stripped = stripped.replace(needle, "")
    stripped = re.sub(r"\{\s*\}", "", stripped)
    return len(stripped.strip()) < 20


def hash_code(value: str) -> int:
    raw = 0
    for char in value:
        raw = (raw * 31 + ord(char)) & 0xFFFFFFFF
    return raw


def redis_client():
    if redis is None:
        return None
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = redis.Redis.from_url(url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def queue_submission(job: dict[str, Any]) -> dict[str, Any]:
    job = dict(job)
    job.setdefault("id", str(uuid.uuid4()))
    client = redis_client()
    if client is not None:
        client.rpush(JOB_QUEUE_KEY, json.dumps(job))
        return {"id": job["id"], "status": "queued"}
    with _MEMORY_LOCK:
        _MEMORY_QUEUE.append(job)
    return {"id": job["id"], "status": "queued"}


def pop_next_job() -> dict[str, Any] | None:
    client = redis_client()
    if client is not None:
        payload = client.lpop(JOB_QUEUE_KEY)
        if payload is None:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None
    with _MEMORY_LOCK:
        if not _MEMORY_QUEUE:
            return None
        return _MEMORY_QUEUE.popleft()


def process_job(job: dict[str, Any]) -> dict[str, Any]:
    problem = fetch_problem_by_id_or_slug(str(job["problemId"]))
    if problem is None:
        return {"status": "Failed", "error": "Problem not found.", "jobId": job.get("id")}
    result = judge_submission(problem, job["language"], str(job["code"]), job.get("mode", "submit"))
    result["jobId"] = job.get("id")
    return result


def worker_loop() -> None:
    while not _WORKER_STOP.is_set():
        job = pop_next_job()
        if job is None:
            time.sleep(0.1)
            continue
        process_job(job)


def start_worker() -> None:
    global _WORKER_THREAD
    if _WORKER_THREAD is not None and _WORKER_THREAD.is_alive():
        return
    _WORKER_THREAD = threading.Thread(target=worker_loop, name="codesoft-worker", daemon=True)
    _WORKER_THREAD.start()


def stop_worker() -> None:
    global _WORKER_THREAD
    _WORKER_STOP.set()
    if _WORKER_THREAD is not None and _WORKER_THREAD.is_alive():
        _WORKER_THREAD.join(timeout=2)


def judge_submission(problem: dict[str, Any], language: str, code: str, mode: str) -> dict[str, Any]:
    starter = (problem.get("starter") or {}).get(language, "")
    edited = normalize_code(code) != normalize_code(starter)
    empty = looks_empty(code)
    tests = problem.get("tests", [])
    if mode == "run" and tests:
        pool = [test for test in tests if test.get("sample")] if any(test.get("sample") for test in tests) else tests[:1]
    else:
        pool = tests

    status = "Accepted"
    if not edited or empty:
        status = "Wrong Answer"
    elif re.search(r"syntax error|undefined_name|;;;;", code, flags=re.IGNORECASE):
        status = "Compilation Error"
    elif re.search(r"while\s*\(\s*true\s*\)|while True", code):
        status = "Time Limit Exceeded"
    elif re.search(r"raise |throw new |segfault", code, flags=re.IGNORECASE):
        status = "Runtime Error"

    seed = hash_code(f"{code}{language}{problem['id']}")
    runtime_ms = 0 if status == "Compilation Error" else 8 + (seed % 90)
    memory_kb = 0 if status == "Compilation Error" else 12000 + (seed % 28000)

    cases: list[dict[str, Any]] = []
    for index, item in enumerate(pool, start=1):
        passed = status == "Accepted"
        cases.append(
            {
                "index": index,
                "input": item.get("input"),
                "expected": item.get("output"),
                "output": item.get("output") if passed else "(empty)" if status == "Wrong Answer" else "",
                "passed": passed,
                "sample": bool(item.get("sample")),
            }
        )

    tests_passed = sum(1 for case in cases if case["passed"])
    return {
        "status": status,
        "runtimeMs": runtime_ms,
        "memoryKb": memory_kb,
        "stdout": "\n".join(case["output"] for case in cases) if status == "Accepted" else "",
        "stderr": (
            "error: expected expression before end of input"
            if status == "Compilation Error"
            else "RuntimeError: mock exception"
            if status == "Runtime Error"
            else ""
        ),
        "testsPassed": tests_passed,
        "testsTotal": len(cases),
        "cases": cases,
        "mode": mode,
        "language": language,
        "problemId": problem["id"],
    }
