# Admin Console implementation plan

**Goal:** Upgrade the existing application into a real, authorized operations console using existing domain data.
**Architecture:** Shared authentication and API client; separate `/admin` layout; FastAPI admin services with bounded queries and transactional audit. PostgreSQL/SQLite-compatible SQLAlchemy models; new tables migrated explicitly without rewriting existing content.
**Spec:** ../specs/2026-09-05-admin-console.md

## Audit mapping
- Existing: shared JWT/password/Google authentication, User/Project/Document/UploadedFile/Template/Job/Automation/AIUsageEvent/UserQuota/AuditLog models; admin endpoints and read-only dashboard.
- Partial: user lock/plan API, task cancellation/retry domain services, usage events, quota checks, template versions, payment checkout.
- Incorrect: frontend admin role differs from backend superuser-only guard; plan_tier lookup differs from User.plan; user usage summary counts other users' documents/sources.
- Hard-coded: provider health, storage, active users, admin AI operations; no correct period comparison.
- Security issue: client confirm-payment grants plan without server evidence; optional auth must reject locked accounts; administrative changes lack actor/reason/before/after.
- Missing: dedicated admin layout, role matrix, typed admin client, filtered/paginated management, safe audited actions, operational health, payment records, server verification.

## Shared contracts
`require_admin` and `require_super_admin` live in app/core/admin_access.py. `is_superuser` means SUPER_ADMIN, otherwise role=admin means ADMIN. Inactive always rejected.
`record_audit(db, actor, action, target_type, target_id, before, after, reason, request=None)` is transactional and allowlists/redacts audit values; no commit inside service.
All lists return `{items, total, page, page_size}`. Dates ISO UTC; filters use `from`, `to`, `search`, `page`, `page_size`, `sort`, `order`. Unavailable observations use null + explanation; no synthetic metric values.
`change_user_plan(db, user, plan, actor, reason, request=None)` in services/admin/plan_service.py validates PLANS, applies existing UserQuota limits preserving usage, audits without committing.
Admin core routes: session, overview, users/detail/update, quotas/update, jobs/detail/action, usage, audit-logs, search.
Operations routes: projects, documents, templates, automations, integrations, system/health, ai-config, providers, settings; operations supplies schemas and action contract to frontend implementer.
Billing routes: plans, payments, billing; safe checkout and provider verified confirmation in existing billing API. Provider absent => Not configured and no automatic upgrade.

## Phase 0 — audit and correctness
- [x] Role matrix tests, lock enforcement, plan lookup consistency, common audit and plan domain service.
- [x] Replace synthetic admin/usage metrics; explicit time boundaries; payment anti-forgery tests and server verification.
## Phase 1 — core
- [x] SQL filtered aggregates, paginated users, user detail, quotas, safe job actions, append-only audit with reason; API tests covering guards, bounds, isolation and mutation transactions.
- [x] Separate AdminLayout > Sidebar/Header/Breadcrumb > route content, typed API, URL filters, table, confirmations and charts; unauthorized never sees admin content.
## Phase 2 — operations
- [x] Paginated metadata-only resource APIs; audited template/automation controls; measured health/integration/configured state with no credentials serialized.
- [x] Dedicated operations screens and reusable data components; unavailable telemetry clearly identified.
## Phase 3 — commercial
- [x] Persistent payments/subscriptions, verification/idempotency, plan/quota consistency, migrations and payment failure tests.
- [x] Plans/payments/subscription management and payment detail.
## Phase 4 — configuration
- [x] Super-admin-only effective configuration; no secret values; only expose writable settings actually consumed by runtime.
- [x] UI permission gates, confirmation, audit and validation for configuration changes.
## Verification and rollout
- [x] Run targeted API tests after each bounded backend module; frontend typecheck/lint/tests/build after integration.
- [x] Browser role/URL/navigation/responsive checks using isolated fixtures; no edits to production user roles.
- [x] Independent review, regression tests, migration test on isolated database, final mapping of shipped/unsupported capabilities.

## Design review
Use neutral surfaces and one compact page header, tables for entities, independent-unit charts for trends. Avoid stacked cards; wrap filters; scroll tables on narrow screens; use explicit metric definitions and unavailable labels. State coverage includes session checking, 401/403, loading skeleton, empty, partial, API errors with retry, success and pending mutations. Reuse existing React/Next/Tailwind/lucide, no large UI dependency.

## Delivery scope
Implementation and validation details, along with unavailable advanced capabilities, are recorded in [admin-console-delivery.md](../admin-console-delivery.md). Checked items describe the bounded work above, not a claim that every advanced feature in the full master prompt is implemented.
