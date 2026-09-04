import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { isSidebarItemActive } from "../sidebarNav.js";

describe("isSidebarItemActive", () => {
  it("activates the create item without also activating projects", () => {
    assert.equal(isSidebarItemActive("/projects/new", "/projects/new"), true);
    assert.equal(isSidebarItemActive("/projects/new", "/projects"), false);
  });

  it("activates projects for the project list and project detail routes", () => {
    assert.equal(isSidebarItemActive("/projects", "/projects"), true);
    assert.equal(isSidebarItemActive("/projects/abc123", "/projects"), true);
  });

  it("keeps the home item exact", () => {
    assert.equal(isSidebarItemActive("/", "/"), true);
    assert.equal(isSidebarItemActive("/projects", "/"), false);
  });

  it("matches ordinary nested dashboard sections", () => {
    assert.equal(isSidebarItemActive("/templates/monthly", "/templates"), true);
    assert.equal(isSidebarItemActive("/documents", "/templates"), false);
  });
});
