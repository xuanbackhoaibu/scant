import test from "node:test";
import assert from "node:assert/strict";

import { formatApiErrorMessage, formatUnknownError } from "../apiErrors.js";

test("formats FastAPI validation detail arrays without object placeholders", () => {
  const message = formatApiErrorMessage({
    detail: [
      {
        loc: ["body", "email"],
        msg: "value is not a valid email address",
        type: "value_error",
      },
    ],
  });

  assert.equal(message.includes("[object Object]"), false);
  assert.match(message, /email/);
  assert.match(message, /value is not a valid email address/);
});

test("formats nested detail objects into useful text", () => {
  const message = formatApiErrorMessage({
    detail: {
      message: "Quota exceeded",
      remaining: 0,
    },
  });

  assert.equal(message.includes("[object Object]"), false);
  assert.match(message, /Quota exceeded/);
  assert.match(message, /remaining: 0/);
});

test("formats thrown objects and object-shaped error messages", () => {
  const thrownObject = formatUnknownError({ detail: [{ loc: ["body", "file"], msg: "required" }] });
  const objectMessage = formatUnknownError({ message: { detail: { message: "Export failed" } } });

  assert.equal(thrownObject.includes("[object Object]"), false);
  assert.match(thrownObject, /file: required/);
  assert.equal(objectMessage.includes("[object Object]"), false);
  assert.match(objectMessage, /Export failed/);
});
