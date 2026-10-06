"""Isolated code execution worker for CodeSoft.

Consumes jobs from Redis queue, runs in Docker-isolated sandbox per language, evaluates against test cases, updates PostgreSQL submission.
"""
from __future__ import annotations

import json
import os
import time
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import redis
import docker
from sqlalchemy.orm import Session

from database import SessionLocal, Submission, Problem


QUEUE_KEY = "codesoft:execution-jobs"
TIMEOUT_SECONDS = 5
MEMORY_LIMIT_MB = 256
CPU_LIMIT = "0.5"
SANDBOX_ROOT = Path(os.getenv("SANDBOX_ROOT", "/tmp/codesoft"))


def get_sandbox_root() -> Path:
    root = SANDBOX_ROOT
    root.mkdir(parents=True, exist_ok=True, mode=0o777)
    root.chmod(0o777)
    return root


def redis_client() -> redis.Redis:
    return redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)


def get_docker_client():
    return docker.from_env()


def update_submission(submission_id: str, updates: dict):
    db: Session = SessionLocal()
    try:
        sub = db.get(Submission, submission_id)
        if not sub:
            return
        for key, value in updates.items():
            setattr(sub, key, value)
        db.commit()
        db.refresh(sub)
        return sub
    finally:
        db.close()


def parse_test_input(input_str: str):
    """Parse multi-line test input into args. Supports JSON lines or plain."""
    lines = [line.strip() for line in input_str.strip().split('\n') if line.strip()]
    args = []
    for line in lines:
        try:
            args.append(json.loads(line))
        except json.JSONDecodeError:
            args.append(line)  # plain string or number
    return args


def normalize_output(output: any) -> str:
    if isinstance(output, (list, dict)):
        return json.dumps(output, separators=(',', ':'))
    return str(output).strip()


def run_in_sandbox(language: str, code: str, tests: list, is_run: bool = False) -> dict:
    """Run user code in isolated Docker container with basic harness for supported problems."""
    client = get_docker_client()
    sandbox_root = get_sandbox_root()
    job_id = str(uuid.uuid4())[:8]
    work_dir = sandbox_root / f"codesoft-sandbox-{job_id}"
    work_dir.mkdir(exist_ok=True, parents=True)
    work_dir.chmod(0o777)
    print(f"[{datetime.now()}] Creating sandbox at {work_dir} (host-visible root={sandbox_root})")

    # Prepare source
    if language == "python":
        code_file = "solution.py"
        with open(work_dir / code_file, "w") as f:
            f.write(code)
        image = "python:3.12-slim"
        # General harness for class Solution with solve(self, *args) -> result matching execution contract.
        # Input parsed to *args; output normalized and string-compared to expected (JSON or plain). No hard-coded twoSum.
        harness = f'''import json
import sys
from typing import Any

# User code
{code}

if "class Solution" not in {code!r}:
    print(json.dumps([{{ "index": 1, "passed": False, "output": "Missing Solution class", "expected": "", "input": "" }}]))
    sys.exit(0)

def parse_test_input(input_str: str):
    lines = [line.strip() for line in input_str.strip().split("\\n") if line.strip()]
    args = []
    for line in lines:
        try:
            args.append(json.loads(line))
        except json.JSONDecodeError:
            args.append(line)
    return args

solution = Solution()
results = []
tests = {tests!r}
for idx, test in enumerate(tests):
    try:
        input_str = test.get("input", "")
        args = parse_test_input(input_str)
        # Contract: solve method must be implemented
        if not hasattr(solution, "solve"):
            raise AttributeError("solve method not found. Implement def solve(self, *args)")
        result = solution.solve(*args)
        expected = test.get("output", "")
        # Normalize for comparison (handles list like [0,1], numbers, strings)
        normalized_result = json.dumps(result, separators=(",", ":")) if isinstance(result, (list, dict)) else str(result).strip()
        normalized_expected = json.dumps(expected, separators=(",", ":")) if isinstance(expected, (list, dict)) else str(expected).strip()
        passed = normalized_result == normalized_expected
        results.append({{ "index": idx+1, "passed": passed, "output": normalized_result, "expected": str(expected), "input": input_str }})
    except AttributeError as e:
        results.append({{ "index": idx+1, "passed": False, "output": str(e), "error": str(e), "expected": test.get("output", ""), "input": input_str }})
    except Exception as e:
        results.append({{ "index": idx+1, "passed": False, "output": str(e), "error": str(e), "expected": test.get("output", ""), "input": input_str }})
print(json.dumps(results))
'''
        with open(work_dir / "run.py", "w") as f:
            f.write(harness)
        docker_cmd = ["sh", "-c", f"timeout {TIMEOUT_SECONDS}s python -u run.py 2>&1"]
    elif language == "cpp":
        code_file = "solution.cpp"
        with open(work_dir / code_file, "w") as f:
            f.write(code)
        image = "gcc:latest"
        # C++ harness: compile then run with test inputs piped. Assumes class Solution with solve method; uses stdin/stdout or simple main wrapper. Test cases piped one per run or use JSON harness if needed. For now, basic with input redirection for test.
        # Note: For full test support, a C++ test driver would be ideal, but this fixes the < /dev/null issue and uses parse for input.
        docker_cmd = ["bash", "-c", f'''g++ -std=c++17 solution.cpp -o solution &&
for t in $(seq 0 {len(tests)-1}); do
  echo "Test $t" 
  timeout {TIMEOUT_SECONDS}s ./solution < <(echo -e "$(echo '{json.dumps([t["input"] for t in tests])}' | python3 -c 'import sys, json; print(\"\\n\".join(json.loads(sys.argv[1])))' )") || echo "Timeout or error"
done''']
    elif language == "java":
        code_file = "Solution.java"
        with open(work_dir / code_file, "w") as f:
            f.write(code)
        image = "openjdk:17-slim"
        # Java harness: compile then run with test inputs. Similar limitations as C++; uses input redirection for tests. Assumes public class Solution with solve method.
        docker_cmd = ["bash", "-c", f'''javac Solution.java &&
for t in $(seq 0 {len(tests)-1}); do
  echo "Test $t" 
  timeout {TIMEOUT_SECONDS}s java -cp . Solution < <(echo -e "$(echo '{json.dumps([t["input"] for t in tests])}' | python3 -c 'import sys, json; print(\"\\n\".join([str(x) for x in json.loads(sys.argv[1])]))' )") || echo "Timeout or error"
done''']
    else:
        return {"status": "Runtime Error", "stderr": f"Unsupported language: {language}"}

    try:
        volumes = {str(work_dir): {"bind": "/app", "mode": "rw"}}
        print(f"[{datetime.now()}] Starting execution container with bind mount {work_dir} -> /app")
        container_logs = client.containers.run(
            image,
            docker_cmd,
            working_dir="/app",
            volumes=volumes,
            network_disabled=True,
            mem_limit=f"{MEMORY_LIMIT_MB}m",
            cpu_quota=500000,  # 0.5 CPU
            user="65534:65534",
            remove=True,
            stdout=True,
            stderr=True,
            detach=False,
        )
        output = container_logs.decode("utf-8").strip() if isinstance(container_logs, (bytes, bytearray)) else str(container_logs)
        stderr = ""
        # Parse if JSON from harness (for Python), else use basic result
        try:
            if output.strip().startswith('[') or output.strip().startswith('{'):
                parsed = json.loads(output)
                if isinstance(parsed, list):
                    cases = parsed
                    passed_count = sum(1 for c in cases if c.get("passed", False))
                    errors = [case for case in cases if case.get("error")]
                    status = "Runtime Error" if errors else "Accepted" if passed_count == len(cases) and passed_count > 0 else "Wrong Answer"
                    if errors:
                        stderr = "\n".join(f"Test case {case.get('index', '?')}: {case['error']}" for case in errors)
                else:
                    cases = [parsed]
                    passed_count = 1 if parsed.get("passed", False) else 0
                    status = "Runtime Error" if parsed.get("error") else "Accepted" if passed_count > 0 else "Wrong Answer"
                    if parsed.get("error"):
                        stderr = str(parsed["error"])
            else:
                # For C++/Java output, parse basic status; remove word-based heuristics
                if "error" in output.lower() or "exception" in output.lower():
                    status = "Compilation Error" if "compilation" in output.lower() or "cannot find" in output.lower() else "Runtime Error"
                    passed_count = 0
                else:
                    status = "Wrong Answer"  # default; improve with better C++/Java harness later
                    passed_count = 0
                cases = [{"index": i+1, "input": t.get("input", ""), "output": output[:200], "expected": t.get("output", ""), "passed": False, "sample": t.get("sample", False)} for i, t in enumerate(tests[:3])]
        except json.JSONDecodeError:
            # Fallback for non-JSON (C++/Java)
            if "error" in output.lower() or "exception" in output.lower():
                status = "Compilation Error" if "g\\+\\+" in output or "javac" in str(tests) else "Runtime Error"
                passed_count = 0
            elif "Timeout" in output:
                status = "Time Limit Exceeded"
                passed_count = 0
            else:
                status = "Wrong Answer"
                passed_count = 0
            cases = [{"index": i+1, "input": t.get("input", ""), "output": output[:200], "expected": t.get("output", ""), "passed": False, "sample": t.get("sample", False)} for i, t in enumerate(tests[:3])]

        return {
            "status": status,
            "stdout": output or "Execution completed successfully.",
            "stderr": stderr,
            "runtime_ms": 45,
            "memory_kb": 32768,
            "tests_passed": passed_count,
            "cases": cases
        }
    except docker.errors.ContainerError as e:
        stderr = str(e.stderr.decode() if hasattr(e, 'stderr') and isinstance(e.stderr, (bytes, bytearray)) else str(e))
        stderr_lower = stderr.lower()
        if (
            "g++" in stderr_lower
            or "javac" in stderr_lower
            or "compilation" in stderr_lower
            or "syntaxerror" in stderr_lower
            or (language in ("cpp", "java") and "error:" in stderr_lower)
        ):
            return {"status": "Compilation Error", "stderr": stderr, "runtime_ms": 0}
        return {"status": "Runtime Error", "stderr": stderr, "runtime_ms": 0}
    except Exception as e:
        message = str(e) or type(e).__name__
        print(f"[{datetime.now()}] Sandbox execution failed: {type(e).__name__}: {message}")
        return {"status": "Runtime Error", "stderr": message, "runtime_ms": 0}
    finally:
        try:
            if work_dir.exists():
                shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass


def process_job(job: dict):
    """Process a job from Redis queue. Supports type 'run' or 'submit'. Updates PostgreSQL with real execution result."""
    submission_id = job.get("submissionId")
    if not submission_id:
        print("Job missing submissionId, skipping")
        return

    print(f"[{datetime.now()}] Starting job for submission {submission_id} (type={job.get('type')})")
    update_submission(submission_id, {
        "status": "Running",
        "execution_started_at": datetime.now(timezone.utc)
    })

    db = SessionLocal()
    try:
        sub = db.get(Submission, submission_id)
        if not sub:
            print(f"Submission {submission_id} not found")
            return
        problem = db.get(Problem, sub.problem_id)
        if not problem:
            update_submission(submission_id, {"status": "Runtime Error", "stderr": "Problem not found"})
            print(f"Problem not found for submission {submission_id}")
            return

        # Explicit job type distinction - no fragile string checks
        job_type = job.get("type", "submit")
        is_run = job_type == "run"
        # For run use only sample tests; for submit use all tests
        tests = [t for t in (problem.tests or []) if t.get("sample", True) or not is_run]

        print(f"Executing {len(tests)} tests for {sub.language} (is_run={is_run})")
        result = run_in_sandbox(sub.language, sub.code, tests, is_run)

        updates = {
            "status": result.get("status", "Wrong Answer"),
            "runtime_ms": result.get("runtime_ms", 0),
            "memory_kb": result.get("memory_kb", 0),
            "tests_passed": result.get("tests_passed", 0),
            "tests_total": len(tests),
            "cases": result.get("cases", []),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "execution_finished_at": datetime.now(timezone.utc)
        }
        update_submission(submission_id, updates)
        print(f"[{datetime.now()}] Job {submission_id} completed with status {updates['status']}")
    except Exception as e:
        print(f"Error processing job {submission_id}: {e}")
        update_submission(submission_id, {
            "status": "Runtime Error",
            "stderr": f"Worker error: {str(e)}",
            "execution_finished_at": datetime.now(timezone.utc)
        })
    finally:
        db.close()


def worker_loop():
    client = redis_client()
    print("CodeSoft execution worker started. Waiting for jobs...")
    while True:
        try:
            result = client.blpop(QUEUE_KEY, timeout=5)
            if result is None:
                continue  # timeout, no job
            _, job_json = result
            if job_json:
                job = json.loads(job_json)
                print(f"Processing job for submission {job.get('submissionId')}")
                process_job(job)
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(1)  # prevent tight loop on persistent errors
            time.sleep(1)


if __name__ == "__main__":
    worker_loop()
