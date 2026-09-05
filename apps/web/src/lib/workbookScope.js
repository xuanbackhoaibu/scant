/** @param {string[]} available @param {string[]} selected
 * @returns {{type: 'sheet', sheet: string} | {type: 'sheets', sheets: string[]} | {type: 'workbook'} | null}
 */
export function buildWorkbookScope(available, selected) {
  const sheets = [...new Set(selected)].filter(name => available.includes(name));
  if (!sheets.length) return null;
  if (sheets.length === available.length) return { type: 'workbook' };
  if (sheets.length === 1) return { type: 'sheet', sheet: sheets[0] };
  return { type: 'sheets', sheets };
}
