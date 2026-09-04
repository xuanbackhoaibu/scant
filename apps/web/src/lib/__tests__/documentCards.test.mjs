import test from "node:test";
import assert from "node:assert/strict";
import { buildDocumentPreview } from "../documentCards.js";

test("builds a paper preview from report sections", () => {
  const preview = buildDocumentPreview({
    title: "Bao cao phan tich luong",
    total_words: 1200,
    sections: [
      { title: "Tong quan", plain_text: "Dong mot ve bo du lieu.\nDong hai ve xu huong." },
      { title: "Chi tiet", plain_text: "Dong ba ve phong ban." },
    ],
  });

  assert.equal(preview.title, "Bao cao phan tich luong");
  assert.equal(preview.sectionCount, 2);
  assert.equal(preview.wordCount, 1200);
  assert.deepEqual(preview.lines.slice(0, 3), ["Tong quan", "Dong mot ve bo du lieu.", "Dong hai ve xu huong."]);
});

test("uses report title when sections are not loaded yet", () => {
  const preview = buildDocumentPreview({
    title: "Tai lieu chua nap chi tiet",
    total_words: 0,
    sections: [],
  });

  assert.equal(preview.sectionCount, 0);
  assert.equal(preview.lines[0], "Tai lieu chua nap chi tiet");
  assert.ok(preview.lines.includes("Chua co noi dung xem truoc."));
});
