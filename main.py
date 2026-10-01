from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
import os

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import Problem, SessionLocal, Submission, User, init_db, problem_to_dict, submission_to_dict
from security import create_access_token, decode_access_token, hash_password, verify_password
from worker import queue_submission

app = FastAPI(title="CodeSoft API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None: init_db()


def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()


def fail(code: int, message: str): raise HTTPException(status_code=code, detail=message)
def public_user(user: User) -> dict[str, Any]: return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "solvedIds": [], "attemptedIds": []}


def token_from_header(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "): fail(401, "Authentication required.")
    return authorization[7:]


def current_user(token: str = Depends(token_from_header), db: Session = Depends(db_session)) -> User:
    try: user_id = decode_access_token(token)["sub"]
    except (jwt.InvalidTokenError, KeyError): fail(401, "Invalid or expired token.")
    user = db.get(User, user_id)
    if not user: fail(401, "User no longer exists.")
    return user


def optional_user(authorization: str | None = Header(default=None), db: Session = Depends(db_session)) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        user_id = decode_access_token(authorization[7:])["sub"]
    except (jwt.InvalidTokenError, KeyError):
        return None
    return db.get(User, user_id)


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin": fail(403, "Administrator access required.")
    return user


def problem_values(payload: dict[str, Any], current: Problem | None = None) -> dict[str, Any]:
    fields = {"slug", "title", "difficulty", "tags", "published", "languages", "description", "examples", "constraints", "starter", "tests"}
    result = {key: value for key, value in payload.items() if key in fields}
    if "inputFormat" in payload: result["input_format"] = payload["inputFormat"]
    if "outputFormat" in payload: result["output_format"] = payload["outputFormat"]
    title = result.get("title", current.title if current else "")
    slug = result.get("slug", current.slug if current else "")
    difficulty = result.get("difficulty", current.difficulty if current else "")
    if not title: fail(422, "A problem title is required.")
    if difficulty not in {"Easy", "Medium", "Hard"}: fail(422, "Difficulty must be Easy, Medium, or Hard.")
    if not slug or any(not (c.islower() or c.isdigit() or c == "-") for c in slug): fail(422, "Slug must contain lowercase letters, digits, and hyphens only.")
    return result


@app.get("/api/health")
def health(db: Session = Depends(db_session)):
    db.execute(select(1)); return {"status": "ok"}


@app.post("/api/auth/login")
def login(payload: dict[str, Any], db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(User.email == str(payload.get("email", "")).strip().lower()))
    if not user or not verify_password(str(payload.get("password", "")), user.password_hash): fail(401, "Invalid email or password.")
    return {"token": create_access_token(user.id, user.role), "user": public_user(user)}


@app.post("/api/auth/register", status_code=201)
def register(payload: dict[str, Any], db: Session = Depends(db_session)):
    name, email, password = str(payload.get("name", "")).strip(), str(payload.get("email", "")).strip().lower(), str(payload.get("password", ""))
    if not name or "@" not in email or len(password) < 8: fail(422, "Name, a valid email, and a password of at least 8 characters are required.")
    user = User(name=name, email=email, password_hash=hash_password(password)); db.add(user)
    try: db.commit()
    except IntegrityError: db.rollback(); fail(409, "An account with that email already exists.")
    return {"token": create_access_token(user.id, user.role), "user": public_user(user)}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)): return public_user(user)


@app.get("/api/problems")
def list_problems(q: str = "", difficulty: str = "all", language: str = "all", includeUnpublished: bool = False, user: User | None = Depends(optional_user), db: Session = Depends(db_session)):
    query = select(Problem)
    if not includeUnpublished or not user or user.role != "admin": query = query.where(Problem.published.is_(True))
    if q: query = query.where(or_(Problem.title.ilike(f"%{q}%"), Problem.slug.ilike(f"%{q}%")))
    items = db.scalars(query.order_by(Problem.title)).all()
    if difficulty != "all": items = [p for p in items if p.difficulty.lower() == difficulty.lower()]
    if language != "all": items = [p for p in items if language in p.languages]
    return [problem_to_dict(p, summary=True) for p in items]


@app.get("/api/problems/{problem_id}")
def get_problem(problem_id: str, db: Session = Depends(db_session)):
    item = db.scalar(select(Problem).where(or_(Problem.id == problem_id, Problem.slug == problem_id), Problem.published.is_(True)))
    if not item: fail(404, "Problem not found.")
    return problem_to_dict(item)


@app.get("/api/admin/problems/{problem_id}")
def admin_problem(problem_id: str, _: User = Depends(require_admin), db: Session = Depends(db_session)):
    item = db.scalar(select(Problem).where(or_(Problem.id == problem_id, Problem.slug == problem_id)))
    if not item: fail(404, "Problem not found.")
    return problem_to_dict(item)


@app.post("/api/admin/problems", status_code=201)
def create_problem(payload: dict[str, Any], _: User = Depends(require_admin), db: Session = Depends(db_session)):
    item = Problem(id=str(payload.get("id") or uuid4()), **problem_values(payload)); db.add(item)
    try: db.commit()
    except IntegrityError: db.rollback(); fail(409, "That problem ID or slug already exists.")
    return problem_to_dict(item)


@app.patch("/api/admin/problems/{problem_id}")
def update_problem(problem_id: str, payload: dict[str, Any], _: User = Depends(require_admin), db: Session = Depends(db_session)):
    item = db.scalar(select(Problem).where(or_(Problem.id == problem_id, Problem.slug == problem_id)))
    if not item: fail(404, "Problem not found.")
    for key, value in problem_values(payload, item).items(): setattr(item, key, value)
    try: db.commit()
    except IntegrityError: db.rollback(); fail(409, "That slug already exists.")
    return problem_to_dict(item)


@app.delete("/api/admin/problems/{problem_id}")
def delete_problem(problem_id: str, _: User = Depends(require_admin), db: Session = Depends(db_session)):
    item = db.scalar(select(Problem).where(or_(Problem.id == problem_id, Problem.slug == problem_id)))
    if not item: fail(404, "Problem not found.")
    db.delete(item); db.commit(); return {"ok": True}


def submit(payload: dict[str, Any], user: User, db: Session, persist: bool) -> dict[str, Any]:
    problem_id, language, code = str(payload.get("problemId", "")), str(payload.get("language", "")), str(payload.get("code", ""))
    item = db.scalar(select(Problem).where(or_(Problem.id == problem_id, Problem.slug == problem_id), Problem.published.is_(True)))
    if not item: fail(404, "Problem not found.")
    if language not in item.languages or not code.strip(): fail(422, "A supported language and non-empty source code are required.")
    if not persist: return {"status": "Queued", "runtimeMs": None, "memoryKb": None, "stdout": "", "stderr": "Queued for the execution service.", "testsPassed": 0, "testsTotal": len([t for t in item.tests if t.get("sample")]), "cases": []}
    result = Submission(user_id=user.id, problem_id=item.id, language=language, code=code, status="Queued", tests_total=len(item.tests)); db.add(result); db.commit()
    try: queue_submission({"submissionId": result.id, "userId": user.id, "problemId": item.id, "language": language, "code": code})
    except Exception:
        result.status, result.stderr = "Queue unavailable", "Redis is unavailable; the submission was saved but not queued."; db.commit(); fail(503, result.stderr)
    db.refresh(result); return submission_to_dict(result)


@app.post("/api/run")
def run_code(payload: dict[str, Any], user: User = Depends(current_user), db: Session = Depends(db_session)): return submit(payload, user, db, False)
@app.post("/api/submissions", status_code=202)
def submit_code(payload: dict[str, Any], user: User = Depends(current_user), db: Session = Depends(db_session)): return submit(payload, user, db, True)


@app.get("/api/submissions")
def list_submissions(user: User = Depends(current_user), db: Session = Depends(db_session)):
    return [submission_to_dict(s) for s in db.scalars(select(Submission).options(joinedload(Submission.problem)).where(Submission.user_id == user.id).order_by(Submission.created_at.desc())).unique().all()]


@app.get("/api/submissions/{submission_id}")
def get_submission(submission_id: str, user: User = Depends(current_user), db: Session = Depends(db_session)):
    item = db.scalar(select(Submission).options(joinedload(Submission.problem)).where(Submission.id == submission_id, Submission.user_id == user.id))
    if not item: fail(404, "Submission not found.")
    return submission_to_dict(item)


@app.get("/api/profile")
def profile(user: User = Depends(current_user), db: Session = Depends(db_session)):
    records = db.scalars(select(Submission).options(joinedload(Submission.problem)).where(Submission.user_id == user.id).order_by(Submission.created_at.desc())).unique().all()
    accepted = [s for s in records if s.status == "Accepted"]
    activity = [0] * 48
    for s in records:
        created = s.created_at if s.created_at.tzinfo else s.created_at.replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - created).days
        if 0 <= days < 48: activity[days] += 1
    return {"name": user.name, "email": user.email, "role": user.role, "solved": len({s.problem_id for s in accepted}), "submissions": len(records), "accepted": len(accepted), "recent": [submission_to_dict(s) for s in records[:8]], "activity": activity}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
