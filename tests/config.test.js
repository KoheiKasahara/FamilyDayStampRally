// Node 内蔵テストランナーで実行（インストール不要）:  node --test
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { loadApp } from "./helpers/load-app.js";

const { CFG } = loadApp();

describe("STAMP_CONFIG の整合性", () => {
  it("totalStamps が areas の数と一致する（config.js の注意書き）", () => {
    assert.equal(CFG.totalStamps, CFG.areas.length);
  });

  it("clearThreshold は 1 以上 totalStamps 以下", () => {
    assert.ok(CFG.clearThreshold >= 1);
    assert.ok(CFG.clearThreshold <= CFG.totalStamps);
  });

  it("エリアの code は重複しない", () => {
    const codes = CFG.areas.map((a) => a.code);
    assert.equal(new Set(codes).size, codes.length);
  });

  it("エリアの key は重複しない（QRの簡易キー）", () => {
    const keys = CFG.areas.map((a) => a.key);
    assert.equal(new Set(keys).size, keys.length);
  });

  it("各エリアに code / key / title / image が揃っている", () => {
    for (const a of CFG.areas) {
      assert.ok(a.code);
      assert.ok(a.key);
      assert.ok(a.title);
      assert.match(a.image, /^images\//);
    }
  });
});
