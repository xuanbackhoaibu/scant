# Admin Console — implementation and rollout

Updated 2026-09-06. The console uses the existing Next.js application and FastAPI API. It is not a separate app or authentication system.

## Files and architecture

New frontend: `apps/web/src/app/admin/{layout.tsx,[[...path]]/page.tsx,admin.css}`, `components/admin/{AdminShell,AdminScreen,AdminPrimitives,ConfigurationEditor}.tsx`, `lib/adminApi.ts`.
The old `(dashboard)/admin/page.tsx` is replaced. Shared `lib/api.ts` exposes the existing authenticated request helper.

New API modules: `api/v1/admin_operations.py`, `admin_billing.py`; rebuilt `admin.py`. New services under `services/admin`: query, core, operations, plan, audit, configuration. `admin_service.py` retains the compatibility read facade without synthetic metrics.
New models: `admin_billing.py` and `admin_configuration.py`. Shared gates: `core/admin_access.py`; trusted request identity: `core/usage_context.py`.
Modified existing auth/dependencies, billing adapter/routes and VietQRPaymentModal (hosted PayOS checkout with server verification), quota engine, AI gateway/model router/provider responses, automation attribution, HTTP metrics collector. All modifications are in the existing stack.

## Database / migration

Run from `apps/api`, using the intended deployment `DATABASE_URL`:

```sh
venv/bin/python -m app.migrations.admin_console
```

Back up the deployment database before applying. The migration creates `billing_payments`, `billing_subscriptions`, and `admin_configuration`; adds query indexes; backfills missing quota records in batches from each user's actual plan and current-month recorded usage. Repeating it preserves existing quotas, usage, plans and records. Schema and backfill have been tested on an isolated SQLite database, including repeated application. PostgreSQL live rollout/concurrency tests have not been run.

The workspace SQLite database was backed up and migrated successfully: 3 tables checked, 10 indexes checked, 9 missing quota records backfilled. The pre-release subscription payment reference was made nullable while preserving existing rows, allowing audited admin grants without inventing payments. Backup: `/private/tmp/scan-admin-backups/before-admin-edbdg071.sqlite`. No remote/production database was migrated. New startup `create_all` discovers the new tables, but the explicit migration is still required for existing-table indexes and quota backfill. Existing admin roles are preserved; no default admin password or automatic user promotion is introduced.

## Routes and API

UI: `/admin`, `/admin/users[/id]`, `/admin/ai-jobs[/id]`, `/admin/usage`, `/admin/quotas`, `/admin/projects[/id]`, `/admin/documents`, `/admin/storage`, `/admin/templates[/id]`, `/admin/automations[/id]`, `/admin/integrations`, `/admin/billing`, `/admin/billing/plans`, `/admin/payments[/id]`, `/admin/audit-logs`, `/admin/system`, `/admin/ai-config`, `/admin/providers`, `/admin/settings`, `/admin/search`.

API under `/api/v1/admin`: session; overview (dashboard alias); users list/detail/PATCH; usage; quotas list/PATCH; jobs list/detail/cancel; audit-logs; search; projects list/detail; documents/storage/templates/automations lists; template validation/publish/unpublish; automation history/pause/resume; integrations; plans; payments/detail; billing/subscriptions; system/health; providers; ai-config and settings GET/PATCH.

Lists use bounded pagination and server-side SQL filtering/sorting where applicable. Filters are reflected in the URL. Invalid configuration revisions return 409 rather than overwrite another administrator's change. Dates use UTC, with an exclusive end date.

## Permissions and security

- `is_superuser=true` → Super Admin; otherwise `role=admin` → Admin; otherwise User. Inactive accounts cannot use authenticated or optional-auth protected APIs.
- Every admin API checks the database-backed role. Ordinary users cannot render the admin shell. Configuration and role assignment require Super Admin.
- Ordinary admins cannot modify other administrators. Self-lock/self-demotion is blocked; authorization changes serialize before checking the last active Super Admin.
- Administrative mutations require a reason and write actor, target, before/after, IP, user-agent in the same transaction. No audit update/delete endpoints are exposed.
- Document and operational responses use selected metadata fields. No document contents, download URLs, credentials, OAuth tokens or provider keys are serialized.
- Checkout creates persistent server records. Confirmation verifies provider evidence against stored session, owner, order, plan, amount, currency and transaction. A unique transaction and conditional claim prevent replay/double activation. Plan, subscription and quota update together while preserving usage.
- Google login rejects locked accounts before linking and requires a verified email.

## Real measurements

| Measurement | Source / coverage |
| --- | --- |
| Users / registration growth | User rows and creation dates |
| Active users | Distinct authenticated users with AIUsageEvent in the selected period; this is not all logins |
| Jobs | Existing Job rows; current status for jobs created in the period |
| Reports / documents | Report and Document records; does not imply every report was successfully exported |
| Tokens / estimated AI cost / latency | Recorded AIUsageEvent rows, filtered by dates/provider/model/feature/user |
| Per-user usage | Trusted authenticated request context or explicit background job ownership |
| Storage | UploadedFile.file_size; physical filesystem capacity is shown separately |
| Automation | Automation/AutomationRun records and current-process scheduler state |
| Health | Measured DB SELECT latency, filesystem access/capacity, in-process HTTP observations |
| Payment | Server-persisted checkout and verified payment records |

AI Gateway now persists usage outside its retry loop, preventing telemetry failures from replaying a paid request. Gemini/OpenAI adapters return token counters from provider responses; Gemini output includes thinking tokens. Offline demo responses are explicitly tagged and excluded from paid/live usage. Failed-call token costs are not supplied by providers and are not inferred as measured charges. Costs are estimates, not invoices, and exclude taxes, cache discounts, tool charges and account credits. Historical recorded costs are not rewritten.

Gemini standard text rates were checked against [Google's pricing documentation](https://ai.google.dev/gemini-api/docs/pricing), including the Pro input-length tier; [OpenAI's GPT-4o mini documentation](https://developers.openai.com/api/docs/models/gpt-4o-mini) provides the corresponding standard mini rates. Rates remain deployment-managed; runtime configuration does not retroactively reprice events.

## Available workflows

- Independent responsive admin navigation with shared login, access checking, loading/error/empty states, URL filters, pagination, user detail tabs and searches.
- Real overview, usage trends, per-model/feature/provider/user breakdowns, jobs, quotas, projects, documents and storage metadata.
- Lock/unlock, roles, plans, quota overrides/reset, supported job cancellation, template validation/publication, automation pause/resume and execution history, with audit.
- Payment/subscription records and server-verified activation. Unconfigured checkout returns 503 rather than a fake checkout link.
- Super Admin can change registration availability/default plan and gateway task routing/retries/timeouts. These versioned settings are persisted and read by runtime. Provider credentials remain deployment-managed.

## Explicit limitations / remaining capabilities

These are visible as unavailable/read-only or omitted controls, not fabricated successes:

- Job retry and automation Run Once remain unavailable without durable replay/idempotency infrastructure. Cancellation is cooperative at worker checkpoints.
- Legacy direct-provider calls bypass gateway telemetry/configuration. Historical activity cannot be reconstructed where no usage event was recorded. Project attribution still depends on callers supplying project_id; request context provides user identity.
- Quotas currently enforce token and cost counters. Separate OCR-page/report/research/storage quotas, expiring bonuses and exact concurrent token reservations are not implemented.
- No distributed worker heartbeat, Redis/queue collector, historical API time-series store or physical orphan-file reconciliation. Integration configuration does not prove live connectivity; OAuth connected/expired-user counts are not yet collected.
- Template validation checks version/schema or bounded DOCX ZIP/XML integrity. Semantic placeholder compatibility, a dedicated version/archive workflow and content previews are not implemented in admin.
- Provider keys, pricing/catalog changes, refunds, recurring billing and webhook history remain deployment/provider-managed. PayOS requires `PAYOS_CLIENT_ID`, `PAYOS_API_KEY`, `PAYOS_CHECKSUM_KEY` and explicit `PAYOS_PRICE_{PRO,TEAM,ENTERPRISE}_VND`. No real charge/provider credential integration test was performed.
- Quota and database SQL are portable in implementation, but cross-process PostgreSQL concurrency still needs deployment-level verification.

## Verification

API tests cover role matrix, locking, plan/quota/subscription consistency, reason/audit, date filtering/pagination, metadata-only endpoints, unsafe retry rejection, cancellation, template validation, configuration revisions/runtime effect, demo exclusion, trusted usage attribution, monthly rollover and additive repeatable migration. Billing tests cover invalid/unpaid/mismatched/wrong-owner/replayed transactions and unconfigured providers.

Browser acceptance uses a separate SQLite fixture/API and production Next build: anonymous login redirect; User 403 without admin shell; Admin configuration 403; 21 admin routes; search filter/refresh/Back; lock/unlock; mobile menu and horizontal overflow checks. Additional browser checks passed at 768px, in dark mode, for runtime configuration saving and for the unconfigured payment error state without a fake QR. Fixtures are test data, not production metrics.

Final command results are recorded at the end of this document after verification. Existing repository lint warnings are not suppressed.


### Final verification results

- Backend: 49 related tests passed in the final combined run, including both migration regressions.
- Frontend: `npm run typecheck` exit 0; `npm run lint` exit 0 (104 existing repository warnings); `npm test` 68 passed; `npm run build` exit 0.
- Browser: 21 admin routes plus role gates, URL filter/refresh/Back, lock/unlock, 390px mobile, 768px tablet, dark mode, configuration save and unconfigured checkout passed. No uncaught page errors.
- `git diff --check`: exit 0.
- Independent backend review found three concurrency/identity issues; fixes were re-reviewed and regression tests added. Gateway attribution was subsequently addressed with trusted request context and explicit automation ownership.
- Unverified: live PayOS charges, provider network availability, PostgreSQL cross-process concurrency, and the entire unrelated API test suite. No success claim is made for those.
