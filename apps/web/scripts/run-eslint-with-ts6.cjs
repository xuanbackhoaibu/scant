const Module = require("node:module");
const path = require("node:path");
const originalLoad = Module._load;
const ts6 = require("typescript-eslint-ts6");

Module._load = function patchedLoad(request, parent, isMain) {
  const parentPath = parent?.filename || "";
  const isTypeScriptEslint =
    parentPath.includes("/typescript-eslint/") ||
    parentPath.includes("/@typescript-eslint/") ||
    parentPath.includes("/ts-api-utils/") ||
    parentPath.includes("\\typescript-eslint\\") ||
    parentPath.includes("\\@typescript-eslint\\") ||
    parentPath.includes("\\ts-api-utils\\");

  if (request === "typescript" && isTypeScriptEslint) {
    return ts6;
  }

  return originalLoad.call(this, request, parent, isMain);
};

const eslintRoot = path.dirname(require.resolve("eslint/package.json"));
require(path.join(eslintRoot, "bin", "eslint.js"));
