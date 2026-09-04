import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";

const sidebarSource = readFileSync(new URL("../../components/Sidebar.tsx", import.meta.url), "utf8");
const dashboardLayoutSource = readFileSync(
  new URL("../../app/(dashboard)/layout.tsx", import.meta.url),
  "utf8"
);
const projectsLayoutSource = readFileSync(new URL("../../app/projects/layout.tsx", import.meta.url), "utf8");

describe("dashboard sidebar layout", () => {
  it("keeps the primary sidebar fixed while page content scrolls", () => {
    assert.match(sidebarSource, /fixed/);
    assert.doesNotMatch(sidebarSource, /sticky top-14/);
  });

  it("renders dashboards through the shared shell that offsets main content", () => {
    assert.match(dashboardLayoutSource, /DashboardShell/);
    assert.match(projectsLayoutSource, /DashboardShell/);
  });
});
