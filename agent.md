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
- `useMock`: `true` until FastAPI exists — set `false` to send real `fetch` calls
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

## Demo backend status

The project already includes a working FastAPI backend slice in `main.py` with:

- authentication (`/api/auth/*`)
- problem catalog and admin CRUD (`/api/problems`, `/api/admin/problems`)
- profile (`/api/profile`)
- run and submit execution flows (`/api/run`, `/api/submissions`)

This backend uses SQLite persistence in `codesoft.db` and a reusable execution worker in `worker.py`, which keeps the frontend functional without needing the final production execution environment yet. The frontend config has already been switched to real API mode (`useMock: false`).

## Database + worker status

The project now includes:

- SQLite-backed storage for users, problems, and submissions in `database.py`
- a reusable execution judge layer in `worker.py`
- startup seeding for demo accounts and default problem data
- persistence for newly registered users and submitted code results

This is the next staged backend step after the initial demo API: persistent data storage and worker-style judging logic, without yet introducing Redis or isolated sandbox execution.

## Verify locally

```text
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/login.html`.
