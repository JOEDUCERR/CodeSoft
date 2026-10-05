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

### Audit Findings and Implementation of Execution Pipeline

**Current state before changes (from Phase 1 audit):**
- Clicking Run or Submit called `/api/run` or `/api/submissions`, stored "Queued" submission, enqueued to Redis `codesoft:execution-jobs` but worker.py was only a ping loop placeholder.
- No actual execution, no sandbox, no test evaluation, no state updates beyond Queued.
- Frontend (problem.js, submissions.js) used mockJudge when useMock=true; with useMock=false it expected async results but had limited polling.
- Problem model uses class-based starter (Solution.twoSum, etc.) and JSON tests with input/output. Not simple stdin.
- Database Submission had basic fields; added execution timestamps.
- Languages Python, C++, Java declared but unsupported.
- Unsafe direct execution removed earlier; architecture preserved.

**Execution Contract (Phase 2):**
- Problems use LeetCode-style: user implements methods on `Solution` class (twoSum, reverseString, etc.).
- Harness (in runner.py for Python) instantiates Solution, calls method with parsed input (JSON for arrays, int for target), captures return value or modified arg, normalizes with json.dumps for comparison.
- Tests from DB problem.tests (sample for Run, all for Submit).
- Comparison is exact after normalization.
- Supports current 3 problems without major DB changes.

**Implementation (Phases 3-5, 12):**
- runner.py: Redis consumer, Docker sandbox (network_disabled, mem_limit, cpu_quota, user, cap_drop), language-specific prep/harness, timeout, test eval, DB update via SQLAlchemy.
- Python: full harness for twoSum/reverseString style, JSON output for cases.
- C++/Java: basic compile/run (compilation errors caught by Docker error).
- /api/run and /api/submissions return Queued immediately; worker transitions Queued -> Running -> final status.
- Frontend updated minimally for async (statusClass supports Queued/Running); polling not fully added but submission detail polls via GET.
- MockJudge kept for development (useMock=true in config.js for quick UI tests).

**Security (Phase 4):**
- Docker containers with no network, limited CPU/memory, dropped caps, non-root user, tmpfs-like workspace, automatic cleanup with shutil.rmtree.
- No secrets exposed; API only queues; worker uses Docker socket (mounted, required for sandbox).
- Failures update status to prevent stuck "Running".

**Frontend (Phase 7, 12):**
- problem.js shows Queued/Running via status, renders cases.
- submissions.js lists with real statuses.
- No WebSockets; relies on page refresh or manual reload for updates (improvement possible).

**Docs Updates (Phase 13):**
- README.md and agent.md updated with architecture, flow, limitations.
- Added docs/execution-pipeline.md (see below).

**Files Created/Changed:**
- Created: runner.py (main worker/sandbox logic), docs/execution-pipeline.md
- Changed: database.py (added timestamps), main.py (improved submit, job payload), worker.py (simplified), docker-compose.yml (added worker service, Docker socket, fixed DB URL), Dockerfile (added docker.io), requirements.txt (added docker), agent.md, README.md

**Execution Flow:**
Browser -> Nginx/FastAPI (/api/run or /submissions) -> save Submission (Queued) -> Redis queue -> worker.py/runner.py consumes -> Docker sandbox per language with harness -> parse/eval tests -> update Submission in PG -> Frontend GET /api/submissions shows result.

**Supported Languages:** Python (full harness), C++ and Java (basic compile/run; compilation/runtime errors detected).

**Status Lifecycle:** Queued → Running → Accepted | Wrong Answer | Runtime Error | Time Limit Exceeded | Compilation Error (via exception).

**Tests Performed:**
- Manual: docker compose up --build, login, open two-sum, Run with correct Python twoSum, saw Accepted with cases.
- Wrong answer, syntax/runtime (via bad code).
- C++/Java basic (compilation succeeds for valid starter).
- Queue length, DB updates verified via psql/redis-cli.
- Used bash, docker compose logs.

**Verification Commands:**
```bash
docker compose down -v
docker compose up --build -d
docker compose logs worker
curl http://127.0.0.1:8000/api/health
# Login and submit via UI or curl as in README
docker compose exec postgres psql -U codesoft -d codesoft -c "SELECT status, tests_passed FROM submissions ORDER BY created_at DESC LIMIT 5;"
```

**Final Answers to Questions in agent.md:**
1-3. Yes for Python (end-to-end with harness); basic for C++/Java (compiles but harness limited).
4-5. Yes, Run and Submit execute real code against tests, persist results.
6. Yes, incorrect solution -> Wrong Answer.
7. Yes, syntax/runtime/compilation detected.
8. Yes (timeout via Docker).
9. Yes, transitions from Queued.
10. Frontend displays; auto-update limited (refresh for full).
11. Yes, isolated Docker containers.
12. Yes, exceptions caught, status updated, no permanent Queued.
13. Yes, docs accurate for implemented (simulated full harness for Python; basic for others).

**Remaining Limitations:**
- Java/C++ lack full method-specific harness (use Python for full verification).
- Frontend polling not fully implemented for live updates without refresh.
- No memory usage measurement from container stats (fixed value).
- Sandbox shares Docker daemon (socket mount); production would use dedicated runner host or higher isolation (gVisor, Firecracker).
- Only supports current problem set's input style.
- No full test for all edge cases or heavy load.

**Implementation Summary**
- Files created: runner.py, docs/execution-pipeline.md
- Files changed: database.py, main.py, worker.py, docker-compose.yml, Dockerfile, requirements.txt, agent.md, README.md
- Major changes: Added real Redis-consuming runner with Docker sandbox and language runners; fixed DB URLs; added timestamps.
- Execution flow: API queues, worker runs in sandbox, evaluates, updates PG; frontend shows results.
- Supported: Python (complete), C++/Java (basic).
- Status lifecycle as above.
- Verified with docker compose, UI tests for Python Two Sum (correct/wrong/error cases).
- The pipeline now works end-to-end for the main Python flow as per the task.

### Verification notes

`python3 -m compileall main.py database.py security.py worker.py tests` and
`docker compose config --quiet` pass. `docker compose up --build -d` was
verified with `GET /api/health` returning `{"status":"ok"}` and the Redis
queue length command. The suite passes in the supported Python 3.12 Docker
image with `docker compose exec -T backend pytest -q`. The host Python 3.14
test transport stalled before a route invocation, so use the container command
as the reliable verification command for now.
