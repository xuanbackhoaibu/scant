# Production Upgrades Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the production-readiness upgrade sequence for AI Report Studio.

**Architecture:** Keep changes small and aligned with the existing FastAPI/Next.js structure. Add deterministic backend safety behavior first, then expose compact product-facing quality and operations surfaces.

**Tech Stack:** FastAPI, Pydantic Settings, pytest, Next.js, TypeScript.

**Spec:** In-chat approved upgrade sequence: production hardening, AI mode clarity, job progress, report readiness score, observability.

## Global Constraints

- Do not overwrite unrelated dirty work already present in the repository.
- Use focused backend tests for behavior changes.
- Avoid adding new infrastructure dependencies unless the existing code already has a natural hook.

---

### Task 1: Production Hardening

**Files:**
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/app/main.py`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `README.md`
- Test: `apps/api/tests/test_phase_u22_security_hardening.py`

**Interfaces:**
- Produces: `Settings.validate_production_safety() -> list[str]`
- Produces: `Settings.assert_production_safety() -> None`

- [x] Write failing tests for unsafe production config.
- [x] Implement production safety validation.
- [x] Run security/readiness tests.

### Task 2: AI Mode And Telemetry

**Files:**
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/app/services/ai/gateway.py`
- Modify: `apps/api/app/services/ai/gemini_provider.py`
- Modify: `apps/api/app/services/ai/openai_provider.py`
- Test: `apps/api/tests/test_phase_u18_ai_gateway.py`

**Interfaces:**
- Produces: `Settings.is_demo_mode -> bool`
- Produces: `Settings.allow_ai_offline_fallback -> bool`

- [x] Write failing tests that production disables offline mock fallback and records gateway metrics.
- [x] Implement AI mode helpers and provider fallback guards.
- [x] Run AI gateway tests.

### Task 3: Job Progress Foundation

**Files:**
- Modify: `apps/api/app/services/worker/queue_manager.py`
- Modify: `apps/api/app/api/v1/automations.py`
- Test: `apps/api/tests/test_phase_u20_worker_and_checkpoint.py`

**Interfaces:**
- Produces: job progress states with `progress_pct`, `stage`, `retryable`.

- [x] Write failing tests for progress update and retry metadata.
- [x] Implement compact in-memory progress tracking on the existing queue manager.
- [x] Run worker/checkpoint tests.

### Task 4: Report Readiness Score

**Files:**
- Modify: `apps/api/app/services/quality/grounding_guard.py`
- Modify: `apps/api/app/api/v1/reports.py`
- Test: `apps/api/tests/test_grounding_quality_gate.py`

**Interfaces:**
- Produces: `GroundingGuard.readiness_score(validations: list[dict]) -> dict`

- [x] Write failing tests for readiness score grading.
- [x] Implement deterministic readiness score.
- [x] Run quality gate tests.

### Task 5: Observability Middleware

**Files:**
- Modify: `apps/api/app/services/observability/metrics_collector.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_phase_u25_observability.py`

**Interfaces:**
- Produces: HTTP metrics with counts, errors, and latency percentiles.

- [x] Write failing tests for HTTP metric recording.
- [x] Add FastAPI middleware that records request duration and error counts.
- [x] Run observability tests.

### Task 6: Final Verification

**Files:**
- Run test suites directly touched by the plan.

- [x] Run focused backend tests.
- [x] Run secret scanner.
- [x] Review final diff.
