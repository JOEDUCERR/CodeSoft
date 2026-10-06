# CodeSoft frontend — agent context

This file records unique decisions and implementation details for the CodeSoft code-execution platform frontend. Update it when the frontend contract or demo behavior changes.

## Location

All static files live in `frontend/`. Serve that directory as the web root (Nginx `root` or `python -m http.server` from `frontend/`). ES modules require HTTP, not `file://`.

## Stack

Vanilla HTML, CSS, and ES module JavaScript. No bundler, no CSS/JS frameworks. Intended production path: Nginx serves files and reverse-proxies `/api` to FastAPI.

## Brand

Working product name: **CodeSoft**. Compact text logo in the header. Rename later by editing the header brand in `js/components/header.js` and page titles.

## Config

`frontend/js/config.js` is the only place for:

- `apiBase`: `"/api"` (same-origin; no host IPs)
- `useMock`: `false` — the frontend sends requests to the FastAPI backend
- localStorage keys for demo session and overlays

## Auth (demo only)

- Session JSON in `localStorage` (`codesoft.session`). Not security.
- Demo accounts (`data/users.js`):
  - `demo@codesoft.dev` / `demo-pass-1` (user)
  - `admin@codesoft.dev` / `admin-pass-1` (admin)
- Register persists extra users under `codesoft.store.users`.
- Google button is visual only; mock throws / toast, no OAuth client secrets.
- Protected pages redirect to `login.html?next=...`. Admin pages require `role === "admin"`.

## API layer

UI code must not call `fetch` directly. Modules:

- `js/api/client.js` — `request()`, `ApiError`, mock latency
- `js/api/auth.js` — login, register, google, me
- `js/api/problems.js` — list/get + admin save/delete/publish
- `js/api/submissions.js` — list/get, `POST /run`, `POST /submissions`
- `js/api/user.js` — profile
- `js/api/mockJudge.js` — deterministic UI judge (does **not** execute user code)

Expected backend paths match the original contract: `/api/auth/*`, `/api/problems`, `/api/run`, `/api/submissions`, `/api/profile`, `/api/admin/problems`.

## Mock judge behavior

Used only when `useMock` is true:

- Unchanged starter template or near-empty body → **Wrong Answer**
- `syntax error` / `;;;;` → **Compilation Error**
- `while True` / `while(true)` → **Time Limit Exceeded**
- `raise ` / `throw new ` → **Runtime Error**
- Otherwise edited code → **Accepted**

Run uses sample tests; submit uses all tests and appends to `codesoft.store.submissions`.

## Admin overlay

Problem create/edit/delete/publish writes `codesoft.store.problems`. If that key is missing, catalog falls back to `data/problems.js` (15 problems; `kth-largest` is unpublished).

## Pages

| File | Role |
|---|---|
| `login.html` / `register.html` | Auth UI |
| `index.html` | Logged-in home |
| `problems.html` | Filterable table |
| `problem.html` | Workspace (`?id=` slug) |
| `submissions.html` | History + modal (`?id=` optional) |
| `profile.html` | Counts + recent list |
| `admin.html` | Catalog editor |

## CSS

`base.css` tokens, `layout.css` header/workspace, `components.css` table/forms/editor, `pages.css` home/admin. Black/white/gray; semantic green/red/amber only on status.

## Backend status — handoff (2026-10-01)

This work is on the `complete-backend` branch. The frontend is in real API
mode (`frontend/js/config.js` has `useMock: false`), and `main.py` serves both
the static frontend and the FastAPI `/api` routes.

### Implemented

- PostgreSQL-backed SQLAlchemy models in `database.py`: `User`, `Problem`, and
  `Submission`. The application defaults to PostgreSQL; SQLite exists only for
  the automated tests through `DATABASE_URL`.
- Startup creates schema and seeds three published problems plus the demo user
  and admin account. This seed data is backend-owned, not read from frontend
  JavaScript modules.
- Argon2 password hashing and signed JWT bearer authentication in `security.py`.
  `JWT_SECRET` must be set to a strong secret outside local development.
- Auth (`/api/auth/register`, `/login`, `/me`), public catalogue/retrieval,
  profile, and admin problem CRUD routes.
- Submission ownership is enforced: users can only list/read their own
  submissions; admin-only problem routes require an admin JWT.
- `docker-compose.yml` provisions FastAPI, PostgreSQL 16, and Redis 7 with
  health checks and persistent volumes.
- Redis queue adapter in `worker.py`; submitted jobs are pushed to
  `codesoft:execution-jobs`.
- Basic API tests live in `tests/test_api.py`; `README.md` contains commands
  for Docker, curl smoke tests, Redis queue inspection, and pytest.

### Execution pipeline architecture and fixes (2026-10-06)

This repo uses a queue-based execution pipeline:

- Frontend -> FastAPI (`main.py`) -> Redis (`codesoft:execution-jobs`) -> worker (`runner.py`) -> Docker sandbox -> PostgreSQL (`submissions`).
- `main.py` writes a `Submission` as `Queued` and enqueues a JSON payload with `submissionId`, `problemId`, `language`, `code`, and `type` (`run` or `submit`).
- `runner.py` consumes the queue with `blpop`, updates the submission to `Running`, executes user code in Docker, and persists the final status/result back to PostgreSQL.
- The worker connects to Redis via `REDIS_URL`, and to Docker via `/var/run/docker.sock` mounted from the host.

#### Current sandbox architecture

- The worker creates a temporary workspace under a host-visible root (`SANDBOX_ROOT`, default `/tmp/codesoft`).
- In Docker Compose, both the backend and worker mount the same host directory:
  - `/var/run/docker.sock:/var/run/docker.sock`
  - `/tmp/codesoft:/tmp/codesoft`
- Each job creates a unique directory such as `/tmp/codesoft/codesoft-sandbox-<job-id>`.
- That directory is bind-mounted into the execution container at `/app`.

This matters because the Docker daemon sees host paths, not container-internal paths. The previous implementation created sandboxes under `Path.cwd()`, which can resolve to a worker-container path that the host Docker daemon cannot access reliably. The fix keeps the sandbox root explicitly on the host and then mounts that exact host directory into the execution container.

#### Actual root cause for the Runtime Error

The worker was also generating the Python harness with invalid Python literal data. The harness wrote:

```python
tests = {json.dumps(tests)}
```

inside an embedded Python script. That produced `true`/`false` values in lowercase JSON syntax, which is invalid Python and caused the generated `run.py` to crash before it could emit the test result. The worker then swallowed the underlying failure, surfaced a generic `Runtime Error`, and left the submission in an infrastructure error state instead of preserving the real reason.

The fix is:

- create the sandbox under a host-visible root (`/tmp/codesoft`)
- mount that host directory into each execution container as `/app`
- generate the harness with valid Python literals (`tests = {tests!r}`)
- keep diagnostic logging for future debugging

#### Security constraints preserved

- execution containers run with `network_disabled=True`
- memory and CPU limits are still enforced (`mem_limit=256m`, `cpu_quota=500000`)
- the execution container is started as a non-root user (`user="65534:65534"` when possible)
- the worker still does not expose the Docker socket to user code
- each sandbox is temporary and removed in `finally`
- the code does not additionally mount the host root or the Docker socket into the sandbox

#### Validation commands

```bash
docker compose up --build -d
docker compose logs --tail=200 worker
curl -X POST http://localhost:8000/api/auth/register ...
curl -X POST http://localhost:8000/api/run ...
curl http://localhost:8000/api/submissions/<id>
```

#### Known limits

- Python execution is the fully-working path for the current CodeSoft flow.
- C++/Java support remains basic and is not the target of this runtime-error fix.
- The app still relies on polling rather than websockets for live updates.
- The repository intentionally leaves the unrelated Redis/pytest host-environment issue outside this task.
