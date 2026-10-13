# CodeSoft backend explanation

This document explains how the current CodeSoft backend works and where a developer should look when extending it. It is written for someone who is comfortable with basic Python but may be new to FastAPI, Redis, queues, or code-execution services.

## 1. Big-picture architecture

The project has three main layers:

1. **Frontend** — static HTML, CSS, and JavaScript under `frontend/`.
2. **API application** — `main.py`, which exposes FastAPI routes and serves the frontend.
3. **Persistence and execution** — `database.py` stores data, while `worker.py` evaluates submitted code.

In local development, one Uvicorn process runs the FastAPI application:

```text
Browser
  |
  | /api requests and static frontend files
  v
main.py (FastAPI + Uvicorn)
  |                  \
  |                   \ reads/writes
  v                    v
worker.py          database.py -> codesoft.db
  |
  +-> Python subprocess for Python submissions
  +-> legacy deterministic judge for C++ and Java
```

The frontend uses the same origin as the API. Requests such as `/api/problems` are handled by FastAPI, while files such as `/login.html` are served from `frontend/`.

## 2. What happens when the server starts

The normal entry point is:

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

When `main.py` is imported:

1. `FastAPI(...)` creates the application.
2. `init_db()` creates the SQLite tables if they do not exist.
3. The static frontend directory is mounted at `/`.

During FastAPI startup:

1. `init_db()` runs again safely.
2. `start_worker()` starts the daemon worker thread in `worker.py`.

The database initialization is deliberately safe to call more than once. On a new checkout, it creates `codesoft.db`, the `users`, `problems`, and `submissions` tables, and inserts demo data when those tables are empty.

## 3. File responsibilities

### `main.py`

This is the API entry point and request coordinator. It contains:

- authentication routes under `/api/auth/...`
- problem catalog and admin routes
- profile and submission-history routes
- `/api/run` for trying code against sample tests
- `/api/submissions` for storing and evaluating a submission
- startup initialization and worker startup
- static frontend mounting

`main.py` validates the request, checks authentication, finds the problem, creates a job, invokes the worker layer, and formats the response expected by the frontend.

### `database.py`

This is the SQLite persistence module. It owns:

- the database path: `codesoft.db`
- table creation
- demo users and default problems
- user, problem, and submission fetch/update helpers

Records are stored as JSON in a `data` column. This is intentionally simple for the current development stage. It makes it easy to preserve the existing frontend-shaped objects, but it is not yet a normalized production schema.

### `worker.py`

This is the execution and queue module. It owns:

- the optional Redis connection
- the in-memory fallback queue
- job enqueue/dequeue helpers
- the background worker loop
- problem lookup for jobs
- Python subprocess execution
- fallback judging for languages without a real compiler runtime yet

The important functions are:

| Function | Purpose |
| --- | --- |
| `queue_submission()` | Adds a job to Redis or the in-memory queue |
| `pop_next_job()` | Removes the next queued job |
| `process_job()` | Loads the problem and runs the judge |
| `judge_submission()` | Selects Python execution or the legacy judge |
| `start_worker()` | Starts the background queue-draining thread |

### `requirements.txt`

This lists the Python runtime dependencies:

- FastAPI for the HTTP API
- Uvicorn for the development server
- Redis Python client for optional Redis connectivity

Installing the Python package does not install or start a Redis server. Redis is optional in the current local setup.

### `frontend/js/config.js`

This controls the frontend API mode. It is currently configured with `useMock: false`, so the browser calls the FastAPI routes rather than the frontend-only mock judge.

### `agent.md`

This is the short project context and milestone record. Update it when the architecture, frontend contract, or backend capabilities change. Keep detailed implementation guidance in this file.

## 4. Authentication flow

The current authentication is intentionally development/demo-oriented:

1. The browser posts an email and password to `/api/auth/login`.
2. `main.py` looks up the user in SQLite.
3. On success it returns a token shaped like `demo.u_demo`.
4. The frontend sends that token as `Authorization: Bearer demo.u_demo`.
5. `auth_token_from_header()` extracts the token.
6. `get_current_user()` validates the `demo.<user-id>` format and loads the user.

This is not production authentication. Passwords are currently stored in the JSON user record and the token is predictable. A production implementation should use password hashing, signed expiring tokens or server sessions, secret management, and proper authorization checks.

## 5. Database behavior

The SQLite file is created beside the Python files:

```text
codesoft.db
```

The three current tables are:

- `users(id, data)`
- `problems(id, data)`
- `submissions(id, data)`

The `data` values are JSON documents. For example, a submission contains its problem, language, source code, status, test counts, and execution cases.

Important behavior:

- New users are inserted by `/api/auth/register`.
- Admin problem changes are written by the `/api/admin/problems` routes.
- `/api/submissions` first inserts a `Pending` record, then updates it with the result.
- Accepted submissions add the problem ID to the user's `solvedIds`.
- Existing database contents are preserved on restart.

To reset local demo data, stop the server and delete only the project database file:

```powershell
Remove-Item .\codesoft.db
```

The next server start recreates and reseeds it. Do not do this if you need to preserve local registrations or submissions.

## 6. Queue and Redis behavior

`worker.py` supports two queue backends:

### Redis path

If the `redis` Python package is installed and a Redis server is reachable at `REDIS_URL`, `redis_client()` returns a connected client. The default URL is:

```text
redis://localhost:6379/0
```

`queue_submission()` serializes the job as JSON and pushes it to the Redis list:

```text
codesoft:jobs
```

`pop_next_job()` removes one JSON job from that list and decodes it.

To use another Redis server:

```powershell
$env:REDIS_URL = "redis://localhost:6379/0"
python -m uvicorn main:app --port 8000
```

### In-memory fallback

If Redis is not installed, cannot be reached, or `REDIS_URL` is unavailable, the code uses a process-local `deque`. This is convenient for development, but it has important limitations:

- jobs disappear when the process stops
- another API process cannot see the queue
- it is not suitable for multiple worker machines
- it has no durable retry or dead-letter behavior

The fallback is why the backend can run locally without installing Redis.

### Background worker

`start_worker()` launches a daemon thread. The thread repeatedly:

1. calls `pop_next_job()`
2. sleeps briefly if there is no job
3. calls `process_job(job)` when a job is available

`stop_worker()` is available for controlled shutdown, although normal Uvicorn shutdown relies on the process ending.

### Important current limitation

The API currently enqueues a job and then immediately calls `process_job(job)` itself:

```text
request -> queue_submission(job) -> process_job(job) -> response
```

That design keeps the existing frontend contract simple because `/api/run` and `/api/submissions` return a completed result immediately. It also means the same queued job can later be picked up by the background worker, so the current queue is an architectural stepping stone rather than a complete asynchronous job system.

The next proper queue stage should choose one of these designs:

1. **Synchronous local mode:** do not enqueue jobs when processing inline.
2. **Asynchronous production mode:** enqueue once, return `Pending` plus a job ID, process only in the worker, and add a status endpoint or polling mechanism.

Do not mix both paths without deduplication and explicit job state tracking.

## 7. Code execution behavior

### Python

For Python submissions, `judge_submission()` calls `_run_python_case()` for each selected test:

1. It identifies a known method name such as `twoSum`, `search`, or `reverseString`, or finds the first function definition.
2. It writes the submitted source to a temporary `.py` file.
3. It starts a separate Python subprocess.
4. The subprocess imports the temporary module, creates `Solution`, calls the selected method, and prints the result.
5. The parent process compares the output to the expected test output.
6. The temporary file is deleted.
7. The subprocess has a short timeout.

`run` evaluates sample tests where available. `submit` evaluates the complete test list and persists the result.

### C++ and Java

C++ and Java currently use `_legacy_judge()`. This is deterministic placeholder behavior based on the submitted text. It does not compile or execute C++ or Java code yet.

The next language-runtime milestone should add compiler discovery, temporary build directories, compile-time limits, runtime limits, captured stdout/stderr, and isolation. It should not simply call a compiler on untrusted code from the API process.

### Security warning

The current Python subprocess is not a hardened sandbox. A submitted program can potentially access the local filesystem, environment, or network. Do not expose this service to untrusted users or the public internet until container/OS-level isolation, resource limits, filesystem restrictions, and network restrictions are implemented.

## 8. Useful local commands

### Install dependencies

From the repository root:

```powershell
python -m pip install -r requirements.txt
```

### Start the backend

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

If port 8000 is already in use:

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

Open:

```text
http://127.0.0.1:8000/login.html
```

Use `8001` in the URL if that is the port selected.

### Import check

This checks that Python can load the application without starting a server:

```powershell
python -c "import main; print('import-ok')"
```

### Health check

With the server running:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health
```

### Login check

```powershell
$body = '{"email":"demo@codesoft.dev","password":"demo-pass-1"}'
Invoke-RestMethod http://127.0.0.1:8000/api/auth/login -Method Post -ContentType 'application/json' -Body $body
```

The response should contain a token such as `demo.u_demo`.

### List public problems

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/problems
```

### Test a Python run

```powershell
$token = 'demo.u_demo'
$code = "class Solution:`n    def search(self, nums, target):`n        left, right = 0, len(nums) - 1`n        while left <= right:`n            mid = (left + right) // 2`n            if nums[mid] == target: return mid`n            if nums[mid] < target: left = mid + 1`n            else: right = mid - 1`n        return -1"
$body = @{ problemId = 'binary-search'; language = 'python'; code = $code } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/run -Method Post -Headers @{ Authorization = "Bearer $token" } -ContentType 'application/json' -Body $body
```

### Submit code and inspect history

Use the same request shape with `/api/submissions`:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/submissions -Method Post -Headers @{ Authorization = "Bearer $token" } -ContentType 'application/json' -Body $body
Invoke-RestMethod http://127.0.0.1:8000/api/submissions -Headers @{ Authorization = "Bearer $token" }
```

## 9. How to tell what is working

| Check | Expected result |
| --- | --- |
| `import main` | Prints `import-ok` |
| `/api/health` | Returns `{"status":"ok"}` |
| Demo login | Returns a `demo.<id>` token |
| `/api/problems` | Returns seeded published problems |
| `/api/run` with valid Python | Returns `Accepted` or `Wrong Answer` with test cases |
| `/api/submissions` | Creates and returns a persisted submission |
| Restart server | Users, problems, and submissions remain in SQLite |
| Redis unavailable | API still starts using the in-memory fallback |

Signs that a feature is not complete:

- C++ or Java results are not real compiler results yet.
- Jobs are not yet fully asynchronous; the API waits for `process_job()`.
- The local queue is not durable when Redis is unavailable.
- Execution is not secure enough for untrusted public submissions.
- There is no production authentication or password hashing.

## 10. Recommended next development steps

For the next backend iteration, work in this order:

1. Add explicit job records and states: `queued`, `running`, `completed`, and `failed`.
2. Choose synchronous or asynchronous processing rather than doing both for the same job.
3. Add a submission/job status endpoint and frontend polling if asynchronous execution is selected.
4. Persist worker errors and implement bounded retries.
5. Add isolated execution using containers or another OS-level sandbox.
6. Add real C++ and Java runtime handlers.
7. Replace demo authentication with hashed passwords and signed, expiring sessions.
8. Move from JSON blobs in SQLite to a normalized production database when the data model stabilizes.
