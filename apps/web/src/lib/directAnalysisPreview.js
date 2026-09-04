export function resolveSelectedSheetName(workbook, currentSheetName = "", sheetRange = "") {
  const sheets = Array.isArray(workbook?.sheets) ? workbook.sheets : [];
  const sheetNames = sheets.map((sheet) => sheet?.name).filter(Boolean);
  if (sheetNames.length === 0) return "";

  if (currentSheetName && sheetNames.includes(currentSheetName)) {
    return currentSheetName;
  }

  const rawRange = String(sheetRange || "").trim();
  if (rawRange) {
    const explicitSheet = rawRange.includes("!") ? rawRange.split("!", 1)[0] : rawRange;
    const normalizedExplicit = explicitSheet.replace(/^'|'$/g, "").trim();
    if (normalizedExplicit && sheetNames.includes(normalizedExplicit)) {
      return normalizedExplicit;
    }
  }

  return sheetNames[0];
}

export function buildSelectedVisualWorkbook(rawPreview, selectedSheetName = "") {
  const visualWorkbook = rawPreview?.visual_workbook;
  const sheets = Array.isArray(visualWorkbook?.sheets) ? visualWorkbook.sheets : [];
  if (!visualWorkbook || sheets.length === 0) {
    return { workbook: null, sheet: null, activeIndex: -1, mismatch: false };
  }

  const activeIndex = sheets.findIndex((sheet) => sheet?.name === selectedSheetName);
  if (activeIndex < 0) {
    return { workbook: null, sheet: null, activeIndex: -1, mismatch: Boolean(selectedSheetName) };
  }

  return {
    workbook: {
      ...visualWorkbook,
      active_sheet_index: activeIndex,
      sheets,
    },
    sheet: sheets[activeIndex],
    activeIndex,
    mismatch: false,
  };
}
