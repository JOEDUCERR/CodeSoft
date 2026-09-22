from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="CodeSoft API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_USERS = [
    {
        "id": "u_demo",
        "name": "Amlan",
        "email": "demo@codesoft.dev",
        "password": "demo-pass-1",
        "role": "user",
        "solvedIds": ["two-sum", "reverse-string", "binary-search", "climbing-stairs"],
        "attemptedIds": ["valid-parentheses", "merge-intervals"],
    },
    {
        "id": "u_admin",
        "name": "Admin",
        "email": "admin@codesoft.dev",
        "password": "admin-pass-1",
        "role": "admin",
        "solvedIds": ["two-sum", "binary-search"],
        "attemptedIds": ["two-sum"],
    },
]

EXTRA_USERS: list[dict[str, Any]] = []


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "solvedIds": user.get("solvedIds", []),
        "attemptedIds": user.get("attemptedIds", []),
    }


def all_users() -> list[dict[str, Any]]:
    return [*DEMO_USERS, *EXTRA_USERS]


def find_user_by_email(email: str) -> dict[str, Any] | None:
    key = email.strip().lower()
    for user in all_users():
        if user["email"].lower() == key:
            return user
    return None


def find_user_by_id(user_id: str) -> dict[str, Any] | None:
    for user in all_users():
        if user["id"] == user_id:
            return user
    return None


def auth_token_from_header(authorization: str | None = Header(default=None, alias="Authorization")) -> str | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header.")
    token = authorization.split(" ", 1)[1].strip()
    return token or None


def get_current_user(token: str | None = None) -> dict[str, Any]:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")
    raw = token.strip()
    if not raw.startswith("demo."):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")
    user_id = raw.split(".", 1)[1]
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")
    return user


def optional_current_user(token: str | None = None) -> dict[str, Any] | None:
    if token is None:
        return None
    try:
        return get_current_user(token)
    except HTTPException:
        return None


DEFAULT_PROBLEMS = [
    {
        "id": "two-sum",
        "slug": "two-sum",
        "title": "Two Sum",
        "difficulty": "Easy",
        "tags": ["Array", "Hash Table"],
        "published": True,
        "languages": ["python", "cpp", "java"],
        "description": "Given an array of integers nums and an integer target, return the indices of the two numbers such that they add up to target.",
        "inputFormat": "nums: list of integers\ntarget: integer",
        "outputFormat": "Two indices as a list of integers.",
        "examples": [
            {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"},
            {"input": "nums = [3,2,4], target = 6", "output": "[1,2]"},
        ],
        "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9"],
        "starter": {
            "python": "from typing import List\n\nclass Solution:\n    def twoSum(self, nums: List[int], target: int):\n        pass\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        return {};\n    }\n};\n",
            "java": "import java.util.*;\n\nclass Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}\n",
        },
        "tests": [
            {"input": "[2,7,11,15]\n9", "output": "[0,1]", "sample": True},
            {"input": "[3,2,4]\n6", "output": "[1,2]", "sample": True},
            {"input": "[3,3]\n6", "output": "[0,1]", "sample": False},
        ],
    },
    {
        "id": "reverse-string",
        "slug": "reverse-string",
        "title": "Reverse String",
        "difficulty": "Easy",
        "tags": ["Two Pointers", "String"],
        "published": True,
        "languages": ["python", "cpp", "java"],
        "description": "Write a function that reverses a string by modifying the input array in-place.",
        "inputFormat": "s: array of characters",
        "outputFormat": "The reversed array s.",
        "examples": [{"input": 's = ["h","e","l","l","o"]', "output": '["o","l","l","e","h"]'}],
        "constraints": ["1 <= s.length <= 10^5"],
        "starter": {
            "python": "class Solution:\n    def reverseString(self, s):\n        pass\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nclass Solution {\npublic:\n    void reverseString(vector<char>& s) {\n    }\n};\n",
            "java": "import java.util.*;\n\nclass Solution {\n    public void reverseString(char[] s) {\n    }\n}\n",
        },
        "tests": [
            {"input": '["h","e","l","l","o"]', "output": '["o","l","l","e","h"]', "sample": True},
            {"input": '["H","a","n","n","a","h"]', "output": '["h","a","n","n","a","H"]', "sample": True},
        ],
    },
    {
        "id": "binary-search",
        "slug": "binary-search",
        "title": "Binary Search",
        "difficulty": "Easy",
        "tags": ["Array", "Binary Search"],
        "published": True,
        "languages": ["python", "cpp", "java"],
        "description": "Given a sorted array of integers, return the index of target or -1.",
        "inputFormat": "nums: sorted integer array\ntarget: integer",
        "outputFormat": "Index of target, or -1.",
        "examples": [{"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4"}],
        "constraints": ["1 <= nums.length <= 10^4"],
        "starter": {
            "python": "from typing import List\n\nclass Solution:\n    def search(self, nums: List[int], target: int) -> int:\n        pass\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nclass Solution {\npublic:\n    int search(vector<int>& nums, int target) {\n        return -1;\n    }\n};\n",
            "java": "import java.util.*;\n\nclass Solution {\n    public int search(int[] nums, int target) {\n        return -1;\n    }\n}\n",
        },
        "tests": [
            {"input": "[-1,0,3,5,9,12]\n9", "output": "4", "sample": True},
            {"input": "[-1,0,3,5,9,12]\n2", "output": "-1", "sample": True},
        ],
    },
    {
        "id": "kth-largest",
        "slug": "kth-largest",
        "title": "Kth Largest Element in an Array",
        "difficulty": "Medium",
        "tags": ["Heap", "Array"],
        "published": False,
        "languages": ["python", "cpp", "java"],
        "description": "Find the kth largest element in an array.",
        "inputFormat": "nums: integer array\nk: integer",
        "outputFormat": "The kth largest element.",
        "examples": [{"input": "nums = [3,2,1,5,6,4], k = 2", "output": "5"}],
        "constraints": ["1 <= k <= nums.length"],
        "starter": {
            "python": "from typing import List\n\nclass Solution:\n    def findKthLargest(self, nums: List[int], k: int) -> int:\n        pass\n",
            "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nclass Solution {\npublic:\n    int findKthLargest(vector<int>& nums, int k) {\n        return 0;\n    }\n};\n",
            "java": "import java.util.*;\n\nclass Solution {\n    public int findKthLargest(int[] nums, int k) {\n        return 0;\n    }\n}\n",
        },
        "tests": [{"input": "[3,2,1,5,6,4]\n2", "output": "5", "sample": True}],
    },
]

PROBLEMS = [problem.copy() for problem in DEFAULT_PROBLEMS]

DEFAULT_SUBMISSIONS = [
    {
        "id": "s1",
        "problemId": "two-sum",
        "problemTitle": "Two Sum",
        "language": "python",
        "status": "Accepted",
        "runtimeMs": 42,
        "memoryKb": 17680,
        "createdAt": "2026-09-20T15:12:00.000Z",
        "code": "class Solution:\n    def twoSum(self, nums, target):\n        pass\n",
        "testsPassed": 3,
        "testsTotal": 3,
    },
    {
        "id": "s2",
        "problemId": "binary-search",
        "problemTitle": "Binary Search",
        "language": "cpp",
        "status": "Wrong Answer",
        "runtimeMs": 18,
        "memoryKb": 9200,
        "createdAt": "2026-09-20T14:40:00.000Z",
        "code": "class Solution {\npublic:\n    int search(vector<int>& nums, int target) { return 0; }\n};\n",
        "testsPassed": 1,
        "testsTotal": 2,
    },
]

SUBMISSIONS = [dict(item) for item in DEFAULT_SUBMISSIONS]


def problem_summary(problem: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": problem["id"],
        "slug": problem["slug"],
        "title": problem["title"],
        "difficulty": problem["difficulty"],
        "tags": problem.get("tags", []),
        "published": problem.get("published", True),
        "languages": problem.get("languages", []),
    }


def get_problem_by_id_or_slug(value: str) -> dict[str, Any] | None:
    for problem in PROBLEMS:
        if problem["id"] == value or problem["slug"] == value:
            return problem
    return None


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
    pool = tests[:1] if mode == "run" and len(tests) else tests
    if mode == "run" and any(item.get("sample") for item in tests):
        pool = [test for test in tests if test.get("sample")]

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


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(payload: dict[str, Any]):
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", ""))
    user = find_user_by_email(email)
    if not user or user["password"] != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    return {"token": f"demo.{user['id']}", "user": public_user(user), "demo": True}


@app.post("/api/auth/register")
def register(payload: dict[str, Any]):
    email = str(payload.get("email", "")).strip()
    if find_user_by_email(email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists.")
    name = str(payload.get("name", "")).strip() or "New User"
    password = str(payload.get("password", ""))
    if not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required.")
    user = {
        "id": f"u_{uuid.uuid4().hex[:8]}",
        "name": name,
        "email": email,
        "password": password,
        "role": "user",
        "solvedIds": [],
        "attemptedIds": [],
    }
    EXTRA_USERS.append(user)
    return {"token": f"demo.{user['id']}", "user": public_user(user), "demo": True}


@app.post("/api/auth/google")
def google_login():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google sign-in is a UI placeholder. The backend must complete OAuth.")


@app.get("/api/auth/me")
def me(token: str | None = Depends(auth_token_from_header)):
    user = get_current_user(token)
    return public_user(user)


@app.get("/api/problems")
def list_problems(
    q: str = Query(default=""),
    difficulty: str = Query(default="all"),
    language: str = Query(default="all"),
    includeUnpublished: bool = Query(default=False),
    token: str | None = Depends(auth_token_from_header),
):
    current_user = optional_current_user(token)
    visible = PROBLEMS
    if not includeUnpublished and not (current_user and current_user.get("role") == "admin"):
        visible = [problem for problem in visible if problem.get("published", True)]

    query = q.strip().lower()
    if query:
        visible = [
            problem
            for problem in visible
            if query in problem["title"].lower()
            or any(query in tag.lower() for tag in problem.get("tags", []))
            or query in problem["slug"].lower()
        ]
    if difficulty and difficulty != "all":
        visible = [problem for problem in visible if problem["difficulty"].lower() == difficulty.lower()]
    if language and language != "all":
        visible = [problem for problem in visible if language in problem.get("languages", [])]
    return [problem_summary(problem) for problem in visible]


@app.get("/api/problems/{problem_id}")
def get_problem(problem_id: str):
    problem = get_problem_by_id_or_slug(problem_id)
    if problem is None or not problem.get("published", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    return problem


@app.get("/api/admin/problems/{problem_id}")
def admin_get_problem(problem_id: str, token: str | None = Depends(auth_token_from_header)):
    current_user = get_current_user(token)
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    problem = get_problem_by_id_or_slug(problem_id)
    if problem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    return problem


@app.post("/api/admin/problems")
def admin_create_problem(payload: dict[str, Any], token: str | None = Depends(auth_token_from_header)):
    current_user = get_current_user(token)
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    problem = dict(payload)
    if not problem.get("id"):
        problem["id"] = f"p_{uuid.uuid4().hex[:8]}"
    if not problem.get("slug"):
        problem["slug"] = problem["id"]
    if not problem.get("published"):
        problem["published"] = False
    if "languages" not in problem:
        problem["languages"] = ["python"]
    if "tags" not in problem:
        problem["tags"] = []
    PROBLEMS.insert(0, problem)
    return problem


@app.patch("/api/admin/problems/{problem_id}")
def admin_update_problem(problem_id: str, payload: dict[str, Any], token: str | None = Depends(auth_token_from_header)):
    current_user = get_current_user(token)
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    for index, problem in enumerate(PROBLEMS):
        if problem["id"] == problem_id or problem["slug"] == problem_id:
            PROBLEMS[index].update(payload)
            if "slug" not in PROBLEMS[index] or not PROBLEMS[index]["slug"]:
                PROBLEMS[index]["slug"] = PROBLEMS[index]["id"]
            return PROBLEMS[index]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")


@app.delete("/api/admin/problems/{problem_id}")
def admin_delete_problem(problem_id: str, token: str | None = Depends(auth_token_from_header)):
    current_user = get_current_user(token)
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    for index, problem in enumerate(PROBLEMS):
        if problem["id"] == problem_id or problem["slug"] == problem_id:
            del PROBLEMS[index]
            return {"ok": True}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")


@app.get("/api/profile")
def profile(token: str | None = Depends(auth_token_from_header)):
    user = get_current_user(token)
    accepted = [submission for submission in SUBMISSIONS if submission.get("status") == "Accepted"]
    solved_ids = {submission["problemId"] for submission in accepted}
    recent = sorted(SUBMISSIONS, key=lambda item: item.get("createdAt", ""), reverse=True)[:8]
    activity = [0] * 48
    for submission in SUBMISSIONS:
        created = submission.get("createdAt")
        if not created:
            continue
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            continue
        today = datetime.now(timezone.utc)
        delta_days = max(0, int((today - dt).total_seconds() // (60 * 60 * 24)))
        if delta_days < len(activity):
            activity[delta_days] += 1
    return {
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "solved": len(solved_ids),
        "submissions": len(SUBMISSIONS),
        "accepted": len(accepted),
        "recent": recent,
        "activity": activity,
    }


@app.get("/api/submissions")
def list_submissions(token: str | None = Depends(auth_token_from_header)):
    get_current_user(token)
    return SUBMISSIONS


@app.get("/api/submissions/{submission_id}")
def get_submission(submission_id: str, token: str | None = Depends(auth_token_from_header)):
    get_current_user(token)
    for submission in SUBMISSIONS:
        if submission["id"] == submission_id:
            return submission
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")


@app.post("/api/run")
def run_code(payload: dict[str, Any], token: str | None = Depends(auth_token_from_header)):
    get_current_user(token)
    problem_id = str(payload.get("problemId", "")).strip()
    language = str(payload.get("language", "python")).strip()
    code = str(payload.get("code", ""))
    problem = get_problem_by_id_or_slug(problem_id)
    if problem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    if language not in problem.get("languages", []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported language for this problem.")
    return judge_submission(problem, language, code, mode="run")


@app.post("/api/submissions")
def submit_code(payload: dict[str, Any], token: str | None = Depends(auth_token_from_header)):
    user = get_current_user(token)
    problem_id = str(payload.get("problemId", "")).strip()
    language = str(payload.get("language", "python")).strip()
    code = str(payload.get("code", ""))
    problem = get_problem_by_id_or_slug(problem_id)
    if problem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    if language not in problem.get("languages", []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported language for this problem.")

    result = judge_submission(problem, language, code, mode="submit")
    submission = {
        "id": f"s_{uuid.uuid4().hex[:8]}",
        "problemId": problem["id"],
        "problemTitle": problem["title"],
        "language": language,
        "status": result["status"],
        "runtimeMs": result["runtimeMs"],
        "memoryKb": result["memoryKb"],
        "createdAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "code": code,
        "testsPassed": result["testsPassed"],
        "testsTotal": result["testsTotal"],
        "cases": result["cases"],
    }
    SUBMISSIONS.insert(0, submission)
    if result["status"] == "Accepted":
        current = find_user_by_id(user["id"])
        if current:
            solved_set = set(current.get("solvedIds", []))
            solved_set.add(problem["id"])
            current["solvedIds"] = sorted(solved_set)
    return submission


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
