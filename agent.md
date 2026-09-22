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

## Connecting the backend later

1. Implement FastAPI routes under `/api`.
2. Nginx: `location /api { proxy_pass http://fastapi; }`
3. Set `config.useMock = false`.
4. Keep `apiBase` as `/api`. Do not hard-code machine IPs.

## Current backend status

The backend is now functional as a real FastAPI app that supports the frontend contract without the mock-only demo path. The current project state includes:

- authentication routes (`/api/auth/login`, `/api/auth/register`, `/api/auth/me`)
- protected profile and admin flows (`/api/profile`, `/api/admin/problems`)
- problem listing and retrieval backed by SQLite data (`/api/problems`, `/api/problems/{id}`)
- run/submit execution paths wired through a reusable worker layer (`/api/run`, `/api/submissions`)
- startup seeding for demo accounts and default problem catalog entries
- persistence for users, problems, and submissions in `database.py`
- background worker processing and queue abstraction in `worker.py`

This is now beyond the initial demo API: the app persists data, evaluates code through a worker, and keeps the frontend in real API mode (`useMock: false`).

## Database layer

`database.py` stores the project’s core records in `codesoft.db`:

- `users` table with accounts and roles
- `problems` table with published/unpublished catalog entries and starter code
- `submissions` table for execution history and persisted results
- startup seeding for demo users and initial benchmark problems

This gives the app a stable data layer and allows user registrations and code submissions to survive restarts.

## Worker + execution layer

`worker.py` now includes a layered execution design:

- `queue_submission()` pushes work into a queue
- `process_job()` resolves the target problem and invokes the judge
- `judge_submission()` evaluates the solution against the problem tests
- Python tasks run via a subprocess and timeout-aware evaluation flow
- optional Redis queue support is available via `REDIS_URL`, with an in-memory queue fallback for local development

This gives the app a reusable execution pipeline that can evolve toward more isolated runtime environments later without breaking the current frontend contract. At the current stage, `/api/run` and `/api/submissions` enqueue each job and then call `process_job()` synchronously so the frontend receives a complete result in the same request. The background worker thread is active for queued jobs, but asynchronous status polling is not implemented yet.

## Known operational note

If port 8000 is busy on Windows, a stale uvicorn process is usually the cause. The fix is to stop the older process or start the app on a different port during local testing.

## Verify locally

```text
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

If 8000 is occupied, use a free port instead, such as:

```text
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

Open `http://127.0.0.1:8000/login.html` (or the chosen port) to validate the frontend against the backend.

## Developer explanation

See [explanation.md](explanation.md) for a longer guide to the request flow, database, queue, worker, execution behavior, file responsibilities, and troubleshooting commands.
