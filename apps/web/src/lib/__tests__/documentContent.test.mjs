import test from "node:test";
import assert from "node:assert/strict";

import { textToTiptapJson } from "../documentContent.js";

test("converts body text paragraphs to justified TipTap nodes", () => {
  const doc = textToTiptapJson("CHƯƠNG 1: TỔNG QUAN\n\nĐây là đoạn nội dung thân bài cần căn đều hai bên.");

  const paragraph = doc.content.find((node) => node.type === "paragraph");

  assert.equal(paragraph.attrs.textAlign, "justify");
  assert.equal(doc.content[0].type, "heading");
});
