from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import (
    delete_problem,
    fetch_all_problems,
    fetch_all_submissions,
    fetch_problem_by_id_or_slug,
    fetch_submission_by_id,
    fetch_user_by_email,
    fetch_user_by_id,
    init_db,
    insert_submission,
    upsert_problem,
    upsert_user,
)
from worker import judge_submission

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="CodeSoft API", version="0.2.0")
init_db()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "solvedIds": user.get("solvedIds", []),
        "attemptedIds": user.get("attemptedIds", []),
    }


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
    user = fetch_user_by_id(user_id)
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


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(payload: dict[str, Any]):
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", ""))
    user = fetch_user_by_email(email)
    if not user or user.get("password") != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    return {"token": f"demo.{user['id']}", "user": public_user(user), "demo": True}


@app.post("/api/auth/register")
def register(payload: dict[str, Any]):
    email = str(payload.get("email", "")).strip()
    if fetch_user_by_email(email):
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
    upsert_user(user)
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
    visible = fetch_all_problems()
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
    problem = fetch_problem_by_id_or_slug(problem_id)
    if problem is None or not problem.get("published", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    return problem


@app.get("/api/admin/problems/{problem_id}")
def admin_get_problem(problem_id: str, token: str | None = Depends(auth_token_from_header)):
    current_user = get_current_user(token)
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    problem = fetch_problem_by_id_or_slug(problem_id)
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
    upsert_problem(problem)
    return problem


@app.patch("/api/admin/problems/{problem_id}")
def admin_update_problem(problem_id: str, payload: dict[str, Any], token: str | None = Depends(auth_token_from_header)):
    current_user = get_current_user(token)
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    problem = fetch_problem_by_id_or_slug(problem_id)
    if problem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    updated = {**problem, **payload}
    if not updated.get("slug"):
        updated["slug"] = updated["id"]
    upsert_problem(updated)
    return updated


@app.delete("/api/admin/problems/{problem_id}")
def admin_delete_problem(problem_id: str, token: str | None = Depends(auth_token_from_header)):
    current_user = get_current_user(token)
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    if not delete_problem(problem_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")
    return {"ok": True}


@app.get("/api/profile")
def profile(token: str | None = Depends(auth_token_from_header)):
    user = get_current_user(token)
    submissions = fetch_all_submissions()
    accepted = [submission for submission in submissions if submission.get("status") == "Accepted"]
    solved_ids = {submission["problemId"] for submission in accepted}
    recent = sorted(submissions, key=lambda item: item.get("createdAt", ""), reverse=True)[:8]
    activity = [0] * 48
    for submission in submissions:
        created = submission.get("createdAt")
        if not created:
            continue
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            continue
        delta_days = max(0, int((datetime.now(timezone.utc) - dt).total_seconds() // (60 * 60 * 24)))
        if delta_days < len(activity):
            activity[delta_days] += 1
    return {
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "solved": len(solved_ids),
        "submissions": len(submissions),
        "accepted": len(accepted),
        "recent": recent,
        "activity": activity,
    }


@app.get("/api/submissions")
def list_submissions(token: str | None = Depends(auth_token_from_header)):
    get_current_user(token)
    return fetch_all_submissions()


@app.get("/api/submissions/{submission_id}")
def get_submission(submission_id: str, token: str | None = Depends(auth_token_from_header)):
    get_current_user(token)
    submission = fetch_submission_by_id(submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")
    return submission


@app.post("/api/run")
def run_code(payload: dict[str, Any], token: str | None = Depends(auth_token_from_header)):
    get_current_user(token)
    problem_id = str(payload.get("problemId", "")).strip()
    language = str(payload.get("language", "python")).strip()
    code = str(payload.get("code", ""))
    problem = fetch_problem_by_id_or_slug(problem_id)
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
    problem = fetch_problem_by_id_or_slug(problem_id)
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
    insert_submission(submission)

    if result["status"] == "Accepted":
        current = fetch_user_by_id(user["id"])
        if current:
            solved_set = set(current.get("solvedIds", []))
            solved_set.add(problem["id"])
            current["solvedIds"] = sorted(solved_set)
            upsert_user(current)
    return submission


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
