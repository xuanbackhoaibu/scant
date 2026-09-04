import test from "node:test";
import assert from "node:assert/strict";
import {
  buildSelectedVisualWorkbook,
  resolveSelectedSheetName,
} from "../directAnalysisPreview.js";

const workbook = {
  sheets: [
    { name: "dslx", row_count: 64, column_count: 8 },
    { name: "HN Chinh T8", row_count: 319, column_count: 22 },
    { name: "HCM t8", row_count: 210, column_count: 28 },
  ],
  visual_workbook: {
    file_name: "google_sheet.xlsx",
    sheets: [
      { name: "dslx", max_row: 64, max_column: 8, cells: [[{ coordinate: "A1", display_value: "dslx" }]] },
      { name: "HN Chinh T8", max_row: 319, max_column: 22, cells: [[{ coordinate: "A1", display_value: "hn" }]] },
      { name: "HCM t8", max_row: 210, max_column: 28, cells: [[{ coordinate: "A1", display_value: "hcm" }]] },
    ],
  },
};

test("keeps the existing selected sheet after workbook load when it exists", () => {
  assert.equal(resolveSelectedSheetName(workbook, "HN Chinh T8", ""), "HN Chinh T8");
});

test("uses an explicit sheet range before falling back to the first sheet", () => {
  assert.equal(resolveSelectedSheetName(workbook, "", "HCM t8!H6:I137"), "HCM t8");
  assert.equal(resolveSelectedSheetName(workbook, "", ""), "dslx");
});

test("builds a visual workbook whose active sheet matches the selected sheet", () => {
  const result = buildSelectedVisualWorkbook(workbook, "HN Chinh T8");

  assert.equal(result.mismatch, false);
  assert.equal(result.activeIndex, 1);
  assert.equal(result.sheet.name, "HN Chinh T8");
  assert.equal(result.sheet.max_row, 319);
  assert.equal(result.workbook.active_sheet_index, 1);
});

test("does not render a visual workbook when selected sheet is missing", () => {
  const result = buildSelectedVisualWorkbook(workbook, "Missing sheet");

  assert.equal(result.mismatch, true);
  assert.equal(result.workbook, null);
  assert.equal(result.sheet, null);
});
