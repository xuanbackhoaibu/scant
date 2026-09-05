import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const componentDir = resolve(process.cwd(), "src/components");

test("DirectAnalysisPromptPanel renders sheet preview and Next button without setup scope controls to open analysis workspace", () => {
  const source = readFileSync(resolve(componentDir, "DirectAnalysisPromptPanel.tsx"), "utf8");
  assert.match(source, /Đã đọc dữ liệu thành công/);
  assert.doesNotMatch(source, /Phạm vi phân tích/);
  assert.match(source, /Tiếp theo: Mở màn phân tích →/);
});

test("ExcelAnalysisWorkspace renders docked prompt bar with suggestions and Analysis button", () => {
  const source = readFileSync(resolve(componentDir, "ExcelAnalysisWorkspace.tsx"), "utf8");
  assert.match(source, /Nhập yêu cầu phân tích/);
  assert.match(source, /locale === "vi" \? "Phân tích" : "Analyze"/);
  assert.match(source, /👑 Giá trị cao nhất/);
  assert.match(source, /💰 Tổng số liệu/);
  assert.match(source, /🔍 Tìm dữ liệu trùng/);
  assert.match(source, /⚠️ Tìm ô trống \/ thiếu/);
  assert.match(source, /📊 Phân tích bất thường/);
});

test("ExcelAnalysisWorkspace renders structured Analysis Findings Banner with Evidence chip and Undo button", () => {
  const source = readFileSync(resolve(componentDir, "ExcelAnalysisWorkspace.tsx"), "utf8");
  assert.match(source, /lastAnalysisResult\.evidence/);
  assert.match(source, /📍.*Nguồn:/);
  assert.match(source, /handleUndoLastAction/);
  assert.match(source, /api\.data\.actionUndo/);
});

test("ExcelAnalysisWorkspace maintains isolated floating Ask AI chat button with default closed state", () => {
  const source = readFileSync(resolve(componentDir, "ExcelAnalysisWorkspace.tsx"), "utf8");
  assert.match(source, /const \[isChatOpen, setIsChatOpen\] = useState(?:<boolean>)?\(false\)/);
  assert.match(source, /locale === "vi" \? "Hỏi AI" : "Ask AI"/);
  assert.match(source, /ExcelAIChatPanel/);
});

test("workbook read-all mode lets Ask AI chat use workbook scope", () => {
  const workspaceSource = readFileSync(resolve(componentDir, "ExcelAnalysisWorkspace.tsx"), "utf8");
  const chatSource = readFileSync(resolve(componentDir, "ExcelAIChatPanel.tsx"), "utf8");

  assert.match(workspaceSource, /buildWorkbookScope\(sheetNames, selectedAnalysisSheets\)/);
  assert.match(workspaceSource, /setSelectedAnalysisSheets\(\[\.\.\.sheetNames\]\)/);
  assert.match(workspaceSource, /chatScope=\{analysisScope/);
  assert.match(chatSource, /chatScope\?: \{ type: "sheet" \| "sheets" \| "workbook"; sheet\?: string; sheets\?: string\[\] \}/);
  assert.match(chatSource, /formData\.append\("scope", JSON\.stringify\(chatScope\)\)/);
});
