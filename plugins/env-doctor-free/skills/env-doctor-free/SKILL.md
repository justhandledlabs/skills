---
name: env-doctor-free
description: Diagnose local project environment issues that prevent apps from starting or running. Use when the user says "why won't this run", "check my environment", "env doctor", "diagnose startup issue", "it works on my machine", or asks for help debugging missing dependencies, runtime versions, port conflicts, .env problems, file permissions, or stopped services.
metadata:
  version: 1.0.0
  author: JustHandled Labs
  triggers:
  - why won't this run
  - check my environment
  - env doctor
  - diagnose startup issue
  - it works on my machine
---
# Env Doctor

Diagnose the local environment before changing application code. Treat the project as innocent until the environment is ruled out.

## Workflow

1. Detect project type from files:
   - Node: `package.json`
   - Python: `requirements.txt`, `pyproject.toml`, `Pipfile`, or `manage.py`
   - Go: `go.mod`
   - Docker: `Dockerfile` or `docker-compose.yml`
2. Check runtime availability and versions:
   - Node: `node --version` and `npm --version`
   - Python: `python --version` or `python3 --version`
   - Go: `go version`
   - Docker: `docker --version` and `docker compose version`
3. Check dependencies:
   - Node projects with no `node_modules/`: flag as high priority and suggest `npm install`.
   - Python projects with no `.venv/`, `venv/`, or active virtual environment: flag and suggest creating one, then installing requirements.
   - Go projects: run `go mod tidy` only after explaining it mutates `go.mod`/`go.sum`; otherwise suggest it as the fix.
   - Docker projects: check whether Docker is running before suggesting rebuilds.
4. Check common port conflicts for `3000`, `3001`, `5000`, `8000`, and `8080`.
   - On macOS/Linux, suggest `lsof -i :<port>`.
   - On Windows PowerShell, suggest `Get-NetTCPConnection -LocalPort <port>`.
   - If port `3000` is in use, explicitly include `lsof -i :3000` in the fix commands.
5. Validate environment variables:
   - Compare `.env.example` against `.env` when both or either exist.
   - Flag missing `.env` if `.env.example` exists.
   - Flag missing required variables listed in `.env.example`.
   - Always flag missing `DATABASE_URL` when it appears in `.env.example` but is absent from `.env`.
6. Check file permissions:
   - Verify the project directory is writable before running installers or build commands.
   - For Unix-like scripts referenced by `package.json`, `Makefile`, Docker, or shell commands, check whether executable bits may be required and suggest `chmod +x <script>`.
7. Check background services when the project appears to need them:
   - Postgres: referenced by `DATABASE_URL`, `postgres`, `pg`, `psycopg`, Prisma, Django, Rails-like config, or `docker-compose.yml`.
   - Redis: referenced by `REDIS_URL`, `redis`, Celery, BullMQ, Sidekiq-like config, or `docker-compose.yml`.
   - MySQL: referenced by `MYSQL_URL`, `mysql`, `mysqlclient`, `pymysql`, or `docker-compose.yml`.
   - Prefer non-destructive status checks. Suggest start commands only after identifying the likely service.

## Reference Loading

Read `references/checks.md` when the project type is known, when the user asks for a checklist, or when framework-specific `.env` validation is needed for Express, Django, Gin, or Flask.

## Output Shape

Return a prioritized checklist, highest impact first:

```markdown
**Env Doctor Findings**

1. [High] <issue>
   Evidence: `<command output or file reference>`
   Fix:
   ```bash
   <copy-pasteable command>
   ```

2. [Medium] <issue>
   Evidence: `<command output or file reference>`
   Fix:
   ```bash
   <copy-pasteable command>
   ```

**Likely Start Command**
`<command>`

**What I Checked**
Node/Python/Go/Docker runtimes, dependencies, ports, .env, permissions, services.
```

If no issue is found, say that the environment looks healthy and identify the next best application-level debugging step.

## Required Quality Cases

- Missing `node_modules/` in a Node project must be reported with `npm install`.
- Port `3000` in use must be reported with `lsof -i :3000` as a fix/inspection command.
- Missing `DATABASE_URL` in `.env`, when required by `.env.example`, must be reported as a high-priority environment variable issue.
