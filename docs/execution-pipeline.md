# CodeSoft Execution Pipeline

## Architecture Overview

- **Frontend**: Vanilla JS (problem.html, problem.js) calls /api/run or /api/submissions.
- **FastAPI (main.py)**: Validates, creates Submission (Queued), enqueues JSON job to Redis (`codesoft:execution-jobs`).
- **Redis**: Durable queue for jobs.
- **Worker (runner.py)**: Consumes jobs, updates status to Running, runs in Docker sandbox, evaluates tests, updates PG with result.
- **PostgreSQL**: Stores Problems (with tests, starter), Submissions (status, results, cases JSON).
- **Sandbox**: Docker containers per job (isolated, no network, limits).

No code execution in API container.

## Redis Job Format

```json
{
  "submissionId": "uuid",
  "userId": "uuid",
  "problemId": "two-sum",
  "language": "python",
  "code": "...",
  "type": "submit"  // or run
}
```

## Worker Lifecycle

1. blpop from queue.
2. Fetch Submission + Problem.
3. Set Running + started_at.
4. Prepare code + language-specific Docker run with harness.
5. Capture output, parse test results (JSON for Python).
6. Set final status, results, finished_at.
7. Cleanup workspace.

Errors set appropriate status (never leaves in Running).

## Sandbox

- Image per language (python:3.12-slim, gcc, openjdk).
- `network_disabled=True`, `mem_limit=256m`, `cpu_quota=0.5`, non-root, drop all caps.
- Tmp workspace mounted, cleaned with shutil.rmtree.
- Timeout via `timeout` command inside container.
- No Docker socket access from user code.

## Language Runners & Execution Contract

Problems are class-based (Solution.twoSum(nums, target) etc.).

- **Python**: Write harness in run.py that imports user code, calls method with parsed input (JSON for lists), captures return/modified value, outputs JSON array of per-test results.
- **C++**: Compile & run (basic; full harness would require template or stdin-based).
- **Java**: Compile & run (basic).

Test input parsed from multi-line string (JSON or plain). Output normalized with json.dumps for comparison. Sample tests for Run, full for Submit.

## Status Transitions

Queued → Running → Accepted / Wrong Answer / Compilation Error / Runtime Error / Time Limit Exceeded / ...

Frontend uses statusClass for coloring; renders cases in output pane.

## Security Boundaries

- User code never runs in API or worker process.
- Container limits prevent DoS.
- No secrets in containers.
- Read-only where possible (though rw for simplicity).

## Testing

See agent.md for commands. Python Two Sum works end-to-end. C++/Java basic support.

## Limitations

See agent.md.

This document complements agent.md and README.md.
