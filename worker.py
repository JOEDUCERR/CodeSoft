from __future__ import annotations

import re
from typing import Any


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
