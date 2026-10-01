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

### Deliberately deferred: isolated execution pipeline

The old backend ran submitted Python directly in the FastAPI container and
used deterministic C++/Java fallbacks. That was unsafe and was removed.
`POST /api/submissions` now stores a `Queued` submission then enqueues it in
Redis; `/api/run` validates and reports the same queued execution boundary.

The next task is a separate sandbox runner which consumes
`codesoft:execution-jobs`, runs source in constrained language containers
(network disabled, CPU/memory/PID/time limits, read-only filesystem), and
updates the matching PostgreSQL submission with status, output, and test-case
details. Do not restore direct `subprocess` execution to `main.py` or
`worker.py`.

### Verification notes

`python3 -m compileall main.py database.py security.py worker.py tests` and
`docker compose config --quiet` pass. `docker compose up --build -d` was
verified with `GET /api/health` returning `{"status":"ok"}` and the Redis
queue length command. The suite passes in the supported Python 3.12 Docker
image with `docker compose exec -T backend pytest -q`. The host Python 3.14
test transport stalled before a route invocation, so use the container command
as the reliable verification command for now.
