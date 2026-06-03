import assert from "node:assert/strict";
import test from "node:test";

import {
  applyServerArgsToEnv,
  parseServerArgs,
} from "./serverArgs.mjs";

test("parseServerArgs accepts direct backend port and host flags", () => {
  assert.deepEqual(
    parseServerArgs(["--port=4190", "--host", "0.0.0.0"]),
    {
      port: 4190,
      host: "0.0.0.0",
      shutdownAfterMs: null,
      help: false,
    }
  );
});

test("parseServerArgs accepts an explicit shutdown duration", () => {
  assert.deepEqual(
    parseServerArgs(["--shutdown-after", "12h"]),
    {
      port: null,
      host: "",
      shutdownAfterMs: 12 * 60 * 60 * 1000,
      help: false,
    }
  );
  assert.throws(() => parseServerArgs(["--shutdown-after", "forever"]), /positive duration/);
});

test("parseServerArgs rejects removed root-dir flags", () => {
  assert.throws(
    () => parseServerArgs(["--root-dir", "/tmp/models"]),
    /--root-dir has been removed/
  );
});

test("applyServerArgsToEnv preserves env while keeping CLI port in parsed args", () => {
  const result = applyServerArgsToEnv({
    argv: ["--port", "4190"],
    cwd: "/tmp/workspace",
    env: {
      VIEWER_ASSET_BACKEND: "local-fs",
    },
  });

  assert.equal(result.args.port, 4190);
  assert.equal(result.env.VIEWER_ASSET_BACKEND, "local-fs");
});

test("parseServerArgs rejects invalid ports", () => {
  assert.throws(() => parseServerArgs(["--port", "99999"]), /TCP port/);
});
