import test from "node:test";
import assert from "node:assert/strict";
import { selectProjectPreviewReport } from "../projectCards.js";

test("selects the newest report for a project preview", () => {
  const selected = selectProjectPreviewReport(
    { id: "project-1" },
    [
      { id: "report-old", project_id: "project-1", updated_at: "2026-08-20T10:00:00Z" },
      { id: "report-other", project_id: "project-2", updated_at: "2026-08-30T10:00:00Z" },
      { id: "report-new", project_id: "project-1", updated_at: "2026-08-30T09:00:00Z" },
    ]
  );

  assert.equal(selected.id, "report-new");
});

test("returns null when a project has no reports", () => {
  assert.equal(selectProjectPreviewReport({ id: "project-1" }, [{ id: "report-other", project_id: "project-2" }]), null);
});
