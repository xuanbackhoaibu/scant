export function buildSheetDataSignals(sheetNames, analysisBySheet = {}, visualWorkbook) {
  return sheetNames.map((name) => {
    const analysis = analysisBySheet[name];
    const overview = analysis?.overview || null;
    const visualSheet = findVisualSheet(name, visualWorkbook);
    const visualRows = Number(visualSheet?.max_row || visualSheet?.cells?.length || 0);
    const visualColumns = Number(visualSheet?.max_column || visualSheet?.cells?.[0]?.length || 0);
    const visualPopulatedCells = countVisualPopulatedCells(visualSheet);
    const totalRows = Number(overview?.total_rows ?? visualRows);
    const totalColumns = Number(overview?.total_columns ?? visualColumns);
    const populatedCells = Number(overview?.populated_cells ?? visualPopulatedCells);
    const emptyCells = Number(overview?.empty_cells ?? Math.max(totalRows * totalColumns - populatedCells, 0));
    const issueCount = Array.isArray(analysis?.data_quality_issues) ? analysis.data_quality_issues.length : 0;

    return {
      name,
      isRead: Boolean(analysis),
      hasData: populatedCells > 0 || totalRows > 0 || totalColumns > 0,
      totalRows,
      totalColumns,
      populatedCells,
      emptyCells,
      issueCount,
    };
  });
}

function countVisualPopulatedCells(sheet) {
  const rows = Array.isArray(sheet?.cells) ? sheet.cells : [];
  return rows.reduce((total, row) => {
    if (!Array.isArray(row)) return total;
    return (
      total +
      row.filter((cell) => {
        const value = cell?.display_value ?? cell?.value;
        return value !== null && value !== undefined && String(value).trim() !== "";
      }).length
    );
  }, 0);
}

function findVisualSheet(name, visualWorkbook) {
  const sheets = Array.isArray(visualWorkbook?.sheets) ? visualWorkbook.sheets : [];
  return sheets.find((sheet) => String(sheet?.name || "").trim() === name);
}
