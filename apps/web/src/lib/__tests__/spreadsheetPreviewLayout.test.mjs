import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const testDir = dirname(fileURLToPath(import.meta.url));
const componentDir = resolve(testDir, "../../components");
const appDir = resolve(testDir, "../../app");

test("direct analysis preview card constrains spreadsheet overflow internally", () => {
  const source = readFileSync(resolve(componentDir, "DirectAnalysisPromptPanel.tsx"), "utf8");

  assert.match(source, /<div className="min-w-0 space-y-4 overflow-hidden">/);
  assert.match(
    source,
    /className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs min-w-0 overflow-hidden"/
  );
  assert.match(source, /className="h-\[clamp\(360px,45vh,520px\)\] min-h-0 min-w-0 max-w-full overflow-hidden/);
  assert.match(source, /className="flex min-w-0 items-center gap-2 text-sm font-bold text-slate-900"/);
});

test("spreadsheet viewport scrolls wide sheets without stretching its parent", () => {
  const source = readFileSync(resolve(componentDir, "SpreadsheetPreview.tsx"), "utf8");

  assert.match(source, /className="relative flex-1 min-h-0 min-w-0 max-w-full overflow-auto/);
  assert.match(source, /maxWidth: "100%"/);
  assert.match(source, /contain: "inline-size"/);
  assert.match(source, /width: `\$\{totalSheetWidth \* zoom \/ 100\}px`/);
});

test("spreadsheet sheet tabs expose an inline action slot for workbook-level actions", () => {
  const source = readFileSync(resolve(componentDir, "SpreadsheetPreview.tsx"), "utf8");
  const workspaceSource = readFileSync(resolve(componentDir, "ExcelAnalysisWorkspace.tsx"), "utf8");

  assert.match(source, /sheetTabsAction\?: React\.ReactNode/);
  assert.match(source, /\{sheetTabsAction && <div className="ml-1 shrink-0">\{sheetTabsAction\}<\/div>\}/);
  assert.match(workspaceSource, /sheetTabsAction=\{/);
  assert.match(workspaceSource, /Đọc toàn bộ/);
});

test("read-all mode visually activates every sheet tab and its workbook action", () => {
  const previewSource = readFileSync(resolve(componentDir, "SpreadsheetPreview.tsx"), "utf8");
  const workspaceSource = readFileSync(resolve(componentDir, "ExcelAnalysisWorkspace.tsx"), "utf8");

  assert.match(previewSource, /allSheetsActive\?: boolean/);
  assert.match(previewSource, /const isVisuallyActive = allSheetsActive \|\| isActive/);
  assert.match(previewSource, /isVisuallyActive\s+\?\s+"border-t-2 border-emerald-600 bg-white text-emerald-800 shadow-sm ring-1 ring-slate-200"/);
  assert.match(workspaceSource, /allSheetsActive=\{chatScopeMode === "workbook"\}/);
  assert.match(workspaceSource, /chatScopeMode === "workbook"\s+\?\s+"inline-flex h-8 items-center gap-1.5 whitespace-nowrap rounded-md border border-emerald-300 bg-emerald-50/);
});

test("new project data workflow allows preview column to shrink inside the page grid", () => {
  const source = readFileSync(resolve(appDir, "projects/new/page.tsx"), "utf8");

  assert.match(source, /className="mx-auto min-w-0 w-full max-w-\[1600px\] overflow-x-hidden/);
  assert.match(source, /className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white/);
  assert.match(source, /isDataWorkflow && dataAnalysisBranch === "interactive"/);
  assert.match(source, /"2xl:grid-cols-\[300px_minmax\(0,1fr\)\]"/);
  assert.match(source, /"2xl:grid-cols-\[300px_minmax\(0,1fr\)_340px\]"/);
  assert.match(source, /<div className="min-w-0 space-y-6 overflow-hidden">/);
  assert.match(source, /<div className="min-w-0 space-y-4 overflow-hidden">/);
});

test("direct analysis panel does not duplicate the sheet range selector above the preview", () => {
  const source = readFileSync(resolve(componentDir, "DirectAnalysisPromptPanel.tsx"), "utf8");

  assert.doesNotMatch(source, /Đọc sheet\/range nào\? \(Tùy chọn\)/);
  assert.doesNotMatch(source, /Scope \/ Range \(Optional\)/);
  assert.match(source, /Phạm vi phân tích/);
  assert.match(source, /Sheet \/ vùng cụ thể/);
});

test("projects shell prevents wide route content from creating page-level horizontal scroll", () => {
  const source = readFileSync(resolve(componentDir, "DashboardShell.tsx"), "utf8");

  assert.match(source, /className="min-w-0 flex-1 overflow-x-hidden"/);
  assert.match(source, /"min-w-0 overflow-x-hidden overflow-y-auto transition-\[margin\] duration-200"/);
});
