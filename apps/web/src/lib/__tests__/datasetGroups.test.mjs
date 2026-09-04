import test from "node:test";
import assert from "node:assert/strict";
import { groupDatasetsForDisplay } from "../datasetGroups.js";

test("groups similar datasets under their primary dataset", () => {
  const primary = {
    id: "file-1",
    original_name: "bang_luong.csv",
    metadata_json: {
      dataset_comparison: {
        dataset_group_id: "group-1",
        dataset_role: "primary",
        comparison_status: "primary",
      },
    },
  };
  const similar = {
    id: "file-2",
    original_name: "bang_luong_update.csv",
    metadata_json: {
      dataset_comparison: {
        dataset_group_id: "group-1",
        dataset_role: "similar",
        comparison_status: "similar",
        similarity_score: 0.95,
        primary_file_id: "file-1",
      },
    },
  };

  const groups = groupDatasetsForDisplay([similar, primary]);

  assert.equal(groups.length, 1);
  assert.equal(groups[0].primary.id, "file-1");
  assert.equal(groups[0].variants[0].id, "file-2");
  assert.equal(groups[0].status, "similar");
});

test("keeps unrelated datasets in separate groups", () => {
  const groups = groupDatasetsForDisplay([
    { id: "file-1", original_name: "bang_luong.csv", metadata_json: {} },
    { id: "file-2", original_name: "doanh_thu.csv", metadata_json: {} },
  ]);

  assert.equal(groups.length, 2);
  assert.deepEqual(groups.map((group) => group.primary.id), ["file-1", "file-2"]);
});

test("groups legacy exact duplicate uploads by file hash", () => {
  const groups = groupDatasetsForDisplay([
    {
      id: "file-3",
      original_name: "Bang_luong_nhan_vien_08_2026.xlsx",
      file_hash: "same-hash",
      created_at: "2026-08-30T10:02:00Z",
      metadata_json: {},
    },
    {
      id: "file-1",
      original_name: "Bang_luong_nhan_vien_08_2026.xlsx",
      file_hash: "same-hash",
      created_at: "2026-08-30T10:00:00Z",
      metadata_json: {},
    },
    {
      id: "file-2",
      original_name: "Bang_luong_nhan_vien_08_2026.xlsx",
      file_hash: "same-hash",
      created_at: "2026-08-30T10:01:00Z",
      metadata_json: {},
    },
  ]);

  assert.equal(groups.length, 1);
  assert.equal(groups[0].primary.id, "file-1");
  assert.equal(groups[0].variants.length, 2);
  assert.equal(groups[0].status, "duplicate");
});
