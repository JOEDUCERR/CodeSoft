import os
from pathlib import Path

os.environ["DATABASE_URL"] = f"sqlite:///{Path('/tmp/codesoft-api-test.db')}"
os.environ["JWT_SECRET"] = "test-secret-with-at-least-thirty-two-characters"

from fastapi.testclient import TestClient
import database
import main


def setup_module():
    Path("/tmp/codesoft-api-test.db").unlink(missing_ok=True)
    database.init_db()


def client():
    return TestClient(main.app)


def login(email="demo@codesoft.dev", password="demo-pass-1"):
    response = client().post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["token"]


def test_health_login_and_published_catalog():
    assert client().get("/api/health").json() == {"status": "ok"}
    assert len(client().get("/api/problems").json()) >= 3
    assert client().get("/api/auth/me", headers={"Authorization": f"Bearer {login()}"}).status_code == 200


def test_registration_and_owner_isolation():
    response = client().post("/api/auth/register", json={"name": "New User", "email": "new@example.dev", "password": "safe-password"})
    assert response.status_code == 201
    first_token = response.json()["token"]
    with client() as app:
        submission = app.post("/api/submissions", headers={"Authorization": f"Bearer {first_token}"}, json={"problemId": "two-sum", "language": "python", "code": "class Solution: pass"})
    assert submission.status_code == 202
    assert client().get("/api/submissions", headers={"Authorization": f"Bearer {login()}"}).json() == []


def test_admin_is_required_for_problem_write():
    payload = {"slug": "test-problem", "title": "Test problem", "difficulty": "Easy"}
    assert client().post("/api/admin/problems", json=payload, headers={"Authorization": f"Bearer {login()}"}).status_code == 403
    assert client().post("/api/admin/problems", json=payload, headers={"Authorization": f"Bearer {login('admin@codesoft.dev', 'admin-pass-1')}"}).status_code == 201
