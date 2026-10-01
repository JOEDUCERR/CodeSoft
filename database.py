"""PostgreSQL persistence for CodeSoft (SQLite is supported only in tests)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://codesoft:codesoft@db:5432/codesoft")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase): pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    submissions: Mapped[list["Submission"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    difficulty: Mapped[str] = mapped_column(String(20))
    tags: Mapped[list] = mapped_column(JSON, default=list)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[str] = mapped_column(Text, default="")
    input_format: Mapped[str] = mapped_column(Text, default="")
    output_format: Mapped[str] = mapped_column(Text, default="")
    examples: Mapped[list] = mapped_column(JSON, default=list)
    constraints: Mapped[list] = mapped_column(JSON, default=list)
    starter: Mapped[dict] = mapped_column(JSON, default=dict)
    tests: Mapped[list] = mapped_column(JSON, default=list)


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[str] = mapped_column(ForeignKey("problems.id"), index=True)
    language: Mapped[str] = mapped_column(String(20))
    code: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="Queued")
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    tests_total: Mapped[int] = mapped_column(Integer, default=0)
    cases: Mapped[list] = mapped_column(JSON, default=list)
    stdout: Mapped[str] = mapped_column(Text, default="")
    stderr: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    user: Mapped[User] = relationship(back_populates="submissions")
    problem: Mapped[Problem] = relationship()


STARTER = {"python": "from typing import List\n\nclass Solution:\n    def solve(self):\n        # Write your solution\n        pass\n", "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nclass Solution {\npublic:\n    void solve() {}\n};\n", "java": "class Solution {\n    public void solve() {}\n}\n"}
DEFAULT_PROBLEMS = [
    {"id": "two-sum", "slug": "two-sum", "title": "Two Sum", "difficulty": "Easy", "tags": ["Array", "Hash Table"], "description": "Given an array of integers nums and an integer target, return the indices of the two numbers such that they add up to target.", "inputFormat": "nums: list of integers\ntarget: integer", "outputFormat": "Two indices as a list of integers.", "examples": [{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"}], "constraints": ["2 <= nums.length <= 10^4"], "tests": [{"input": "[2,7,11,15]\n9", "output": "[0,1]", "sample": True}, {"input": "[3,2,4]\n6", "output": "[1,2]", "sample": False}]},
    {"id": "reverse-string", "slug": "reverse-string", "title": "Reverse String", "difficulty": "Easy", "tags": ["Two Pointers", "String"], "description": "Write a function that reverses a string in place.", "inputFormat": "s: array of characters", "outputFormat": "The reversed array.", "examples": [{"input": 's = ["h","e","l","l","o"]', "output": '["o","l","l","e","h"]'}], "constraints": ["1 <= s.length <= 10^5"], "tests": [{"input": '["h","e","l","l","o"]', "output": '["o","l","l","e","h"]', "sample": True}]},
    {"id": "binary-search", "slug": "binary-search", "title": "Binary Search", "difficulty": "Easy", "tags": ["Array", "Binary Search"], "description": "Find a target in a sorted array, returning its index or -1.", "inputFormat": "nums: sorted integer array\ntarget: integer", "outputFormat": "Index of target, or -1.", "examples": [{"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4"}], "constraints": ["1 <= nums.length <= 10^4"], "tests": [{"input": "[-1,0,3,5,9,12]\n9", "output": "4", "sample": True}]},
]


def problem_to_dict(p: Problem, summary: bool = False) -> dict[str, Any]:
    result = {"id": p.id, "slug": p.slug, "title": p.title, "difficulty": p.difficulty, "tags": p.tags, "published": p.published, "languages": p.languages}
    if not summary: result |= {"description": p.description, "inputFormat": p.input_format, "outputFormat": p.output_format, "examples": p.examples, "constraints": p.constraints, "starter": p.starter, "tests": p.tests}
    return result


def submission_to_dict(s: Submission) -> dict[str, Any]:
    return {"id": s.id, "problemId": s.problem_id, "problemTitle": s.problem.title, "language": s.language, "status": s.status, "runtimeMs": s.runtime_ms, "memoryKb": s.memory_kb, "createdAt": s.created_at, "code": s.code, "testsPassed": s.tests_passed, "testsTotal": s.tests_total, "cases": s.cases, "stdout": s.stdout, "stderr": s.stderr}


def init_db() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal.begin() as db:
        from security import hash_password
        if not db.scalar(select(User.id).where(User.email == "demo@codesoft.dev")): db.add(User(name="Demo User", email="demo@codesoft.dev", password_hash=hash_password("demo-pass-1"), role="user"))
        if not db.scalar(select(User.id).where(User.email == "admin@codesoft.dev")): db.add(User(name="Admin", email="admin@codesoft.dev", password_hash=hash_password("admin-pass-1"), role="admin"))
        for item in DEFAULT_PROBLEMS:
            if not db.get(Problem, item["id"]): db.add(Problem(id=item["id"], slug=item["slug"], title=item["title"], difficulty=item["difficulty"], tags=item["tags"], published=True, languages=["python", "cpp", "java"], description=item["description"], input_format=item["inputFormat"], output_format=item["outputFormat"], examples=item["examples"], constraints=item["constraints"], starter=STARTER, tests=item["tests"]))
