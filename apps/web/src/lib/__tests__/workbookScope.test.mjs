import test from 'node:test';
import assert from 'node:assert/strict';
import { buildWorkbookScope } from '../workbookScope.js';
test('scope includes exactly the selected sheets', () => {
 assert.deepEqual(buildWorkbookScope(['A','B','C'], ['B']), {type:'sheet', sheet:'B'});
 assert.deepEqual(buildWorkbookScope(['A','B','C'], ['A','C']), {type:'sheets', sheets:['A','C']});
 assert.deepEqual(buildWorkbookScope(['A','B'], ['A','B']), {type:'workbook'});
});
test('empty and stale selections do not silently analyze every sheet', () => {
 assert.equal(buildWorkbookScope(['A','B'], []), null);
 assert.equal(buildWorkbookScope(['A','B'], ['missing']), null);
 assert.deepEqual(buildWorkbookScope(['A','B'], ['A','A','missing']), {type:'sheet',sheet:'A'});
});

test('saved multi-sheet selection survives session restoration', async () => {
 const { createExcelAnalysisSnapshot, parseExcelAnalysisSnapshot } = await import('../excelAnalysisSession.js');
 const saved = createExcelAnalysisSnapshot({chatScopeMode:'sheets',selectedAnalysisSheets:['A','C']});
 const restored = parseExcelAnalysisSnapshot(JSON.stringify(saved));
 assert.equal(restored.chatScopeMode,'sheets');
 assert.deepEqual(restored.selectedAnalysisSheets,['A','C']);
});
