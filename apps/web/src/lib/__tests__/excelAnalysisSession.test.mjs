import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildExcelAnalysisSessionKey,
  createExcelAnalysisSnapshot,
  parseExcelAnalysisSnapshot,
} from "../excelAnalysisSession.js";

describe("excel analysis session persistence", () => {
  it("builds a stable storage key from the uploaded file identity", () => {
    assert.equal(
      buildExcelAnalysisSessionKey({ fileName: "bao cao xe.xlsx" }),
      "ai_report_studio:excel_analysis_session:bao%20cao%20xe.xlsx"
    );
    assert.equal(
      buildExcelAnalysisSessionKey({ fileName: "a.xlsx", fileId: "file-123" }),
      "ai_report_studio:excel_analysis_session:file-123"
    );
  });

  it("round-trips the latest analysis result, history, and highlight layers", () => {
    const snapshot = createExcelAnalysisSnapshot({
      activeSheetName: "REPORT_XE",
      analysisPrompt: "tất cả dữ liệu trùng",
      activeHighlightColor: "#FEF08A",
      analysisActionStatus: "Đã kiểm tra trùng lặp.",
      chatScopeMode: "workbook",
      analysisHistory: [{ prompt: "tất cả dữ liệu trùng", sheet: "REPORT_XE" }],
      analysisBySheet: {
        REPORT_XE: { overview: { total_rows: 10, total_columns: 4 } },
      },
      analysisLayersBySheet: {
        REPORT_XE: [{ id: "layer_1", cells: ["A1", "A2"], visible: true }],
      },
      lastAnalysisResultBySheet: {
        REPORT_XE: { answer: "Có 1 nhóm trùng.", context: { sheet: "REPORT_XE" } },
      },
    });

    const restored = parseExcelAnalysisSnapshot(JSON.stringify(snapshot));

    assert.equal(restored.activeSheetName, "REPORT_XE");
    assert.equal(restored.analysisPrompt, "tất cả dữ liệu trùng");
    assert.equal(restored.chatScopeMode, "workbook");
    assert.equal(restored.analysisBySheet.REPORT_XE.overview.total_rows, 10);
    assert.equal(restored.lastAnalysisResultBySheet.REPORT_XE.answer, "Có 1 nhóm trùng.");
    assert.deepEqual(restored.analysisLayersBySheet.REPORT_XE[0].cells, ["A1", "A2"]);
    assert.equal(restored.analysisHistory.length, 1);
  });
});
