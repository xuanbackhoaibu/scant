# Excel AI Workspace Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split Excel analysis actions from workbook Q&A while grounding every numeric answer in deterministic workbook queries and evidence.

**Architecture:** Reuse the existing `SpreadsheetQueryEngine` as the shared tool layer. Add deterministic workbook tools, route both `WorkbookChatService` and workspace analysis actions through those tools, and update the React workspace so analysis and chat have distinct UX/state.

**Tech Stack:** FastAPI, openpyxl, pandas, pytest, React, TypeScript, Next.js, Tailwind CSS, Node test runner.

**Spec:** `/Users/chuoi/.codex/attachments/39514b75-1a0d-4f59-96c4-0293b7302899/pasted-text.txt`

## Global Constraints

- Do not create a parallel workbook system when existing services can be extended.
- Do not hardcode payroll-specific columns; use dynamic schema matching.
- Numeric answers must include deterministic evidence.
- Chat read-only questions must not fall back to generic “you can ask me” responses when workbook data is available.
- Destructive workbook mutations require confirmation; UI-only highlights may be offered or applied when explicitly requested.
- Preserve existing duplicate, blank, highlight, sheet resolution, and visual preview behavior.

---

### Task 1: Shared Workbook Query Tools

**Files:**
- Modify: `apps/api/app/services/data/spreadsheet_query_engine.py`
- Test: `apps/api/tests/test_excel_ai_workspace_upgrade.py`

**Interfaces:**
- Produces: `get_workbook_info`, `get_sheet_schema`, `find_column`, `read_range`, `aggregate_column`, `find_top_rows`, `search_rows`, `detect_outliers`, `compare_groups`, all returning structured `evidence`.

- [ ] Write failing tests for sheet/schema/column resolution, aggregate, top row, search, outlier, and evidence.
- [ ] Run the new pytest file and verify failures.
- [ ] Implement minimal deterministic tools in `SpreadsheetQueryEngine`.
- [ ] Re-run the new pytest file and existing spreadsheet tests.

### Task 2: Grounded Workbook Copilot

**Files:**
- Modify: `apps/api/app/services/data/workbook_chat_service.py`
- Test: `apps/api/tests/test_excel_ai_workspace_upgrade.py`

**Interfaces:**
- Consumes: Task 1 query tools.
- Produces: grounded chat responses with `answer`, `context`, `evidence`, `blocks`, `actions`, `pending_actions`, `follow_up_context`, `status_steps`.

- [ ] Write failing tests for “Tổng thực lĩnh?”, “Ai có lương cao nhất?”, “NV007 có thông tin gì?”, follow-up “người đó”, selected range priority, missing sheet suggestion, and pending highlight action.
- [ ] Run the tests and verify failures.
- [ ] Implement intent routing before LLM fallback.
- [ ] Store conversation context for resolved sheet, entity, last result, and ranges.
- [ ] Re-run focused tests and existing workbook chat tests.

### Task 3: Analysis Action Flow

**Files:**
- Modify: `apps/api/app/services/data/workbook_chat_service.py`
- Modify: `apps/api/app/api/v1/data.py`
- Modify: `apps/web/src/lib/api.ts`
- Test: `apps/api/tests/test_excel_ai_workspace_upgrade.py`

**Interfaces:**
- Produces: `/data/workbook-analysis-action` accepting workbook source, prompt, sheet, selected range, returning structured result/actions/evidence.

- [ ] Write failing API/service tests for duplicate, blank, compare ranges, outlier, and selected range analysis.
- [ ] Run tests and verify failures.
- [ ] Add endpoint and route to shared query/action logic.
- [ ] Re-run focused API tests.

### Task 4: Workspace UI Separation

**Files:**
- Modify: `apps/web/src/components/ExcelAnalysisWorkspace.tsx`
- Modify: `apps/web/src/components/ExcelAIChatPanel.tsx`
- Create/Modify: `apps/web/src/lib/__tests__/excelWorkspaceAiLayout.test.mjs`

**Interfaces:**
- Consumes: `/data/workbook-analysis-action` and `/data/workbook-chat`.
- Produces: separate “Phân tích dữ liệu / Chạy phân tích” action surface and “Hỏi AI” chat surface, selected-range context chip, source chips, pending action buttons, dynamic quick prompts.

- [ ] Write source-level regression tests for distinct labels, endpoint usage, selected-range chip, source chips, and quick prompt execution.
- [ ] Run Node tests and verify failures.
- [ ] Update React components with separated state and UI.
- [ ] Re-run Node tests and typecheck.

### Task 5: Final Verification

**Files:**
- No source changes expected.

- [ ] Run focused backend pytest.
- [ ] Run relevant existing backend tests.
- [ ] Run frontend lib tests.
- [ ] Run frontend typecheck.
- [ ] Run frontend build.
- [ ] Run local smoke script when server/API are available.
