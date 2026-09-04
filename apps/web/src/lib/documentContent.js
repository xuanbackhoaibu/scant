function paragraphNode(text) {
  return {
    type: "paragraph",
    attrs: { textAlign: "justify" },
    content: text ? [{ type: "text", text }] : [],
  };
}

function headingNode(text, level) {
  return {
    type: "heading",
    attrs: { level },
    content: [{ type: "text", text }],
  };
}

export function textToTiptapJson(text) {
  const blocks = String(text || "")
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  return {
    type: "doc",
    content: blocks.length
      ? blocks.map((block) => {
          if (/^(CHƯƠNG\s+\d+|LỜI MỞ ĐẦU|LỜI NÓI ĐẦU|TÀI LIỆU THAM KHẢO)/i.test(block)) {
            return headingNode(block, 1);
          }
          if (/^\d+\.\d+\.\d+\s+/.test(block)) {
            return headingNode(block, 3);
          }
          if (/^\d+\.\d+\s+/.test(block)) {
            return headingNode(block, 2);
          }
          return paragraphNode(block);
        })
      : [paragraphNode("")],
  };
}
