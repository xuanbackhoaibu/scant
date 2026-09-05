import test from 'node:test';
import assert from 'node:assert/strict';
import { readAnalysisMode, analysisModeUrl } from '../dataAnalysisNavigation.js';

test('selection is explicit and unknown modes return to selection', () => {
  for (const query of ['', 'analysis=unknown']) assert.equal(readAnalysisMode(new URLSearchParams(query)), null);
  for (const mode of ['direct-analysis', 'docx-report']) {
    const url = analysisModeUrl('mode=auto&type=data_analysis&prompt=hello', mode);
    const params = new URL(url, 'http://localhost').searchParams;
    assert.equal(readAnalysisMode(params), mode);
    assert.equal(params.get('prompt'), 'hello');
  }
});

test('returning to selection removes only analysis mode and preserves context', () => {
  const url = analysisModeUrl('mode=auto&type=data_analysis&workflow=data&analysis=docx-report', null);
  const params = new URL(url, 'http://localhost').searchParams;
  assert.equal(readAnalysisMode(params), null);
  assert.equal(params.get('workflow'), 'data');
  assert.equal(params.get('type'), 'data_analysis');
});
