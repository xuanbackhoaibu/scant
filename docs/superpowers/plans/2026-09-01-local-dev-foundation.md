# Local Dev Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make AI Report Studio easy to run, verify, and demo locally before deeper product upgrades.

**Architecture:** Keep the existing FastAPI and Next.js apps. Add small repo-level scripts that orchestrate existing commands, make demo seeding repeatable, and document the exact local workflow.

**Tech Stack:** zsh/bash, FastAPI, SQLAlchemy async, pytest, Next.js.

**Spec:** In-chat approved Phase 1 of the full upgrade sequence: local one-command run, smoke check, idempotent demo data, and README update.

## Global Constraints

- Do not overwrite unrelated dirty work already present in the repository.
- Do not introduce new infrastructure dependencies.
- Keep scripts readable and portable on macOS local development.
- Use focused tests for behavior changes.

---

### Task 1: Idempotent Demo Seed

**Files:**
- Modify: `apps/api/app/seed_sample.py`
- Test: `apps/api/tests/test_seed_sample.py`

**Interfaces:**
- Produces: `async seed_data() -> dict[str, str]`
- Produces: repeated seed runs keep one demo user, one demo workspace, one demo template, one demo project, and one demo report.

- [ ] Write a failing pytest that calls `seed_data()` twice against a temporary SQLite database and asserts counts remain stable.
- [ ] Run `PYTHONPATH=apps/api ./apps/api/venv/bin/pytest apps/api/tests/test_seed_sample.py -q` and verify the duplicate-data assertion fails.
- [ ] Update `seed_sample.py` to look up existing demo records by stable fields before creating them.
- [ ] Run the focused seed test and verify it passes.

### Task 2: Local Run And Smoke Scripts

**Files:**
- Create: `scripts/dev.sh`
- Create: `scripts/smoke-local.sh`

**Interfaces:**
- Produces: `scripts/dev.sh` starts API on `8050` and web on `3050`, with cleanup on Ctrl+C.
- Produces: `scripts/smoke-local.sh` checks API health and web HTTP response.

- [ ] Add `scripts/dev.sh` with preflight checks for `apps/api/venv/bin/uvicorn` and `apps/web/node_modules`.
- [ ] Add `scripts/smoke-local.sh` with clear failures for API or web downtime.
- [ ] Run `bash -n scripts/dev.sh scripts/smoke-local.sh`.
- [ ] Run `bash scripts/smoke-local.sh` while servers are running and verify it reports both services.

### Task 3: README Local Workflow

**Files:**
- Modify: `README.md`

**Interfaces:**
- Produces: README section showing the fastest local demo path.

- [ ] Update README with one-command dev startup, demo seed, smoke check, and direct URLs.
- [ ] Run `bash scripts/check-secrets.sh`.
- [ ] Review diff to confirm the phase touched only planned files.
