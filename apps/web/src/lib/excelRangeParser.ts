/**
 * Excel Range Parser and Coordinate Utility.
 * Supports standard formats:
 * - 'H6:H137', 'I6:I137', 'H11', 'A1:C20'
 * - 'H:I', '6:137'
 * - "'HN Chính T8'!H6:H137"
 */

export function colLetterToIndex(colLetter: string): number {
  const clean = colLetter.toUpperCase().trim();
  let idx = 0;
  for (let i = 0; i < clean.length; i++) {
    const code = clean.charCodeAt(i);
    if (code >= 65 && code <= 90) {
      idx = idx * 26 + (code - 65 + 1);
    }
  }
  return idx;
}

export function colIndexToLetter(colIdx: number): string {
  let letter = "";
  let temp = colIdx;
  while (temp > 0) {
    const mod = (temp - 1) % 26;
    letter = String.fromCharCode(65 + mod) + letter;
    temp = Math.floor((temp - mod) / 26);
  }
  return letter || "A";
}

export interface ParsedExcelRange {
  valid: boolean;
  raw: string;
  sheetName?: string | null;
  startCol?: string;
  startColIdx?: number;
  startRow?: number;
  endCol?: string;
  endColIdx?: number;
  endRow?: number;
  isSingleCell?: boolean;
  colCount?: number;
  rowCount?: number;
}

export function parseExcelRange(rangeStr: string): ParsedExcelRange {
  let cleanStr = rangeStr.trim();
  let sheetName: string | null = null;

  if (cleanStr.includes("!")) {
    const parts = cleanStr.split("!");
    sheetName = parts[0].trim().replace(/^['"]|['"]$/g, "");
    cleanStr = parts.slice(1).join("!").trim();
  }

  // Standard A1:B10 or H6:H137 or H6
  const standardMatch = cleanStr.match(/^([A-Za-z]+)(\d+)(?::([A-Za-z]+)(\d+))?$/);
  if (standardMatch) {
    const startCol = standardMatch[1].toUpperCase();
    const startRow = parseInt(standardMatch[2], 10);
    const endCol = (standardMatch[3] || startCol).toUpperCase();
    const endRow = parseInt(standardMatch[4] || String(startRow), 10);

    const startColIdx = colLetterToIndex(startCol);
    const endColIdx = colLetterToIndex(endCol);

    const minColIdx = Math.min(startColIdx, endColIdx);
    const maxColIdx = Math.max(startColIdx, endColIdx);
    const minRow = Math.min(startRow, endRow);
    const maxRow = Math.max(startRow, endRow);

    return {
      valid: true,
      raw: rangeStr,
      sheetName,
      startCol: colIndexToLetter(minColIdx),
      startColIdx: minColIdx,
      startRow: minRow,
      endCol: colIndexToLetter(maxColIdx),
      endColIdx: maxColIdx,
      endRow: maxRow,
      isSingleCell: minColIdx === maxColIdx && minRow === maxRow,
      colCount: maxColIdx - minColIdx + 1,
      rowCount: maxRow - minRow + 1,
    };
  }

  return { valid: false, raw: rangeStr, sheetName };
}

export function extractExcelRangesFromText(text: string): string[] {
  const ranges: string[] = [];

  // 1. Normalize voice tokens like "H 6" -> "H6"
  const preNormalized = text.replace(/\b([A-Za-z])\s+(\d+)\b/g, "$1$2");

  // 2. Replace "đến", "tới", "sang", "qua", "to", "-"
  let normalized = preNormalized.replace(
    /([A-Za-z]+\d+)\s*(?:đến|tới|sang|qua|to|-)\s*([A-Za-z]+\d+)/gi,
    "$1:$2"
  );

  // 3. Shorthand "H6 đến 137" -> "H6:H137"
  normalized = normalized.replace(
    /([A-Za-z]+)(\d+)\s*(?:đến|tới|sang|qua|to|-)\s*(\d+)/gi,
    "$1$2:$1$3"
  );

  const pattern = /(?:(?:'[^']+'|[A-Za-z0-9_]+)!)?[A-Za-z]+\d+(?::[A-Za-z]+\d+)?|[A-Za-z]+:[A-Za-z]+/g;
  const matches = normalized.match(pattern) || [];

  for (const m of matches) {
    const parsed = parseExcelRange(m);
    if (parsed.valid && !ranges.includes(m)) {
      ranges.push(m);
    }
  }

  return ranges;
}
