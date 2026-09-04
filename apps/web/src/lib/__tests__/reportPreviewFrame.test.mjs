import test from "node:test";
import assert from "node:assert/strict";
import { buildReportPreviewFrameSrcDoc } from "../reportPreviewFrame.js";

test("wraps real report preview html for thumbnail frames", () => {
  const srcDoc = buildReportPreviewFrameSrcDoc("<main><h1>Báo cáo thật</h1><p>Nội dung từ file</p></main>");

  assert.match(srcDoc, /Báo cáo thật/);
  assert.match(srcDoc, /Nội dung từ file/);
  assert.match(srcDoc, /pointer-events: none/);
  assert.match(srcDoc, /transform-origin: top left/);
});

test("returns empty string when no real preview html exists", () => {
  assert.equal(buildReportPreviewFrameSrcDoc(""), "");
  assert.equal(buildReportPreviewFrameSrcDoc(null), "");
});
