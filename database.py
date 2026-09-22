from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "codesoft.db"

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


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS problems (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )

        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            for user in DEMO_USERS:
                conn.execute(
                    "INSERT INTO users (id, data) VALUES (?, ?)",
                    (user["id"], json.dumps(user)),
                )

        if conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0] == 0:
            for problem in DEFAULT_PROBLEMS:
                conn.execute(
                    "INSERT INTO problems (id, data) VALUES (?, ?)",
                    (problem["id"], json.dumps(problem)),
                )

        if conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 0:
            for submission in DEFAULT_SUBMISSIONS:
                conn.execute(
                    "INSERT INTO submissions (id, data) VALUES (?, ?)",
                    (submission["id"], json.dumps(submission)),
                )


def fetch_all_users() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT data FROM users ORDER BY id").fetchall()
    return [json.loads(row["data"]) for row in rows]


def fetch_user_by_email(email: str) -> dict[str, Any] | None:
    key = email.strip().lower()
    for user in fetch_all_users():
        if user["email"].lower() == key:
            return user
    return None


def fetch_user_by_id(user_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT data FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row["data"])


def upsert_user(user: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (id, data) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET data = excluded.data",
            (user["id"], json.dumps(user)),
        )
    return user


def fetch_all_problems() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT data FROM problems ORDER BY id").fetchall()
    return [json.loads(row["data"]) for row in rows]


def fetch_problem_by_id_or_slug(value: str) -> dict[str, Any] | None:
    for problem in fetch_all_problems():
        if problem["id"] == value or problem["slug"] == value:
            return problem
    return None


def upsert_problem(problem: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO problems (id, data) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET data = excluded.data",
            (problem["id"], json.dumps(problem)),
        )
    return problem


def delete_problem(problem_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM problems WHERE id = ?", (problem_id,)).fetchone()
        if row is not None:
            result = conn.execute("DELETE FROM problems WHERE id = ?", (problem_id,)).rowcount
            return result > 0
        result = conn.execute("DELETE FROM problems WHERE json_extract(data, '$.slug') = ?", (problem_id,)).rowcount
    return result > 0


def fetch_all_submissions() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT data FROM submissions ORDER BY id DESC").fetchall()
    return [json.loads(row["data"]) for row in rows]


def fetch_submission_by_id(submission_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT data FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row["data"])


def insert_submission(submission: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO submissions (id, data) VALUES (?, ?)",
            (submission["id"], json.dumps(submission)),
        )
    return submission


def update_submission(submission: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO submissions (id, data) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET data = excluded.data",
            (submission["id"], json.dumps(submission)),
        )
    return submission
