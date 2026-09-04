const MAX_PREVIEW_LINES = 7;

function normalizeLine(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

export function buildDocumentPreview(report) {
  const sections = Array.isArray(report?.sections) ? report.sections : [];
  const lines = [];

  for (const section of sections) {
    const title = normalizeLine(section?.title);
    if (title) lines.push(title);

    const contentLines = String(section?.plain_text || "")
      .split(/\r?\n/)
      .map(normalizeLine)
      .filter(Boolean);
    lines.push(...contentLines);

    if (lines.length >= MAX_PREVIEW_LINES) break;
  }

  if (lines.length === 0) {
    lines.push(normalizeLine(report?.title) || "Tai lieu moi");
    lines.push("Chua co noi dung xem truoc.");
  }

  return {
    title: normalizeLine(report?.title) || "Tai lieu",
    lines: lines.slice(0, MAX_PREVIEW_LINES),
    sectionCount: sections.length,
    wordCount: Number(report?.total_words || 0),
  };
}
