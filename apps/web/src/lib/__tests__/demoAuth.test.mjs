import test from "node:test";
import assert from "node:assert/strict";

import { DEMO_LOGIN, getDemoLoginPayload } from "../demoAuth.js";

test("provides seeded demo credentials for local login", () => {
  assert.deepEqual(getDemoLoginPayload(), {
    email: "demo@aireportstudio.pro",
    password: "DemoVIP123!",
  });
  assert.equal(DEMO_LOGIN.email, "demo@aireportstudio.pro");
  assert.equal(DEMO_LOGIN.password.length > 0, true);
});
