# CodeSoft

CodeSoft is a vanilla-JavaScript programming-practice UI backed by FastAPI,
PostgreSQL, and Redis. The frontend now uses the API as its source of truth;
users, problems, submissions, and authentication do not depend on browser
localStorage or frontend data modules.

## What is complete

- JWT authentication with Argon2 password hashes.
- PostgreSQL persistence for users, problems, and user-owned submissions.
- Protected admin problem CRUD and published-problem catalogue APIs.
- Redis-backed durable execution-job enqueueing.
- Docker Compose setup for API, PostgreSQL, and Redis.
- Safe execution boundary: the API does not run untrusted code. It saves a
  submission as `Queued` and pushes its job to Redis for the future isolated
  runner/pipeline.

The prior SQLite JSON storage, demo bearer tokens, deterministic C++/Java
judge, and in-process Python subprocess execution are no longer used.

## Run the complete local stack

Prerequisites: Docker Engine with the Compose plugin.

```bash
docker compose up --build
```

Open [http://127.0.0.1:8000/login.html](http://127.0.0.1:8000/login.html).
FastAPI serves the frontend and `/api` routes from the same origin. On first
start, PostgreSQL is seeded with three published problems and these accounts:

```text
User:  demo@codesoft.dev / demo-pass-1
Admin: admin@codesoft.dev / admin-pass-1
```

Stop the stack with `docker compose down`. Data remains in the named
`postgres-data` and `redis-data` volumes. To deliberately erase local data and
start over, run `docker compose down -v`.

Before deploying, set a strong `JWT_SECRET` instead of using the Compose
development default:

```bash
JWT_SECRET='replace-with-a-long-random-secret' docker compose up --build
```

## Test it

With the stack running, the health check should return `{"status":"ok"}`:

```bash
curl http://127.0.0.1:8000/api/health
```

Log in and list the public catalogue:

```bash
TOKEN=$(curl -s http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@codesoft.dev","password":"demo-pass-1"}' | \
  python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')

curl http://127.0.0.1:8000/api/problems
curl http://127.0.0.1:8000/api/auth/me -H "Authorization: Bearer $TOKEN"
```

Submit a job and confirm it is persisted as queued:

```bash
curl -X POST http://127.0.0.1:8000/api/submissions \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"problemId":"two-sum","language":"python","code":"class Solution: pass"}'

curl http://127.0.0.1:8000/api/submissions -H "Authorization: Bearer $TOKEN"
docker compose exec redis redis-cli LLEN codesoft:execution-jobs
```

For automated API tests:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
pytest -q
```

The tests use a temporary SQLite database only to run quickly; the application
stack itself uses PostgreSQL.

## API outline

- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/problems`, `GET /api/problems/{id-or-slug}`
- `GET|POST|PATCH|DELETE /api/admin/problems` (admin token required)
- `POST /api/run`, `POST /api/submissions`
- `GET /api/submissions`, `GET /api/submissions/{id}`, `GET /api/profile`

## Next: execution pipeline

Build a separate, locked-down runner that consumes
`codesoft:execution-jobs`. It should run each language in an isolated
container with CPU, memory, process, and network limits, then update the
matching PostgreSQL submission. Do not execute arbitrary source in the
FastAPI container.
