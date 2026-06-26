import { describe, expect, it } from "vitest";

import "../js/config.js";

const CFG = window.STAMP_CONFIG;

describe("STAMP_CONFIG の整合性", () => {
  it("totalStamps が areas の数と一致する（config.js の注意書き）", () => {
    expect(CFG.totalStamps).toBe(CFG.areas.length);
  });

  it("clearThreshold は 1 以上 totalStamps 以下", () => {
    expect(CFG.clearThreshold).toBeGreaterThanOrEqual(1);
    expect(CFG.clearThreshold).toBeLessThanOrEqual(CFG.totalStamps);
  });

  it("エリアの code は重複しない", () => {
    const codes = CFG.areas.map((a) => a.code);
    expect(new Set(codes).size).toBe(codes.length);
  });

  it("エリアの key は重複しない（QRの簡易キー）", () => {
    const keys = CFG.areas.map((a) => a.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("各エリアに code / key / title / image が揃っている", () => {
    for (const a of CFG.areas) {
      expect(a.code).toBeTruthy();
      expect(a.key).toBeTruthy();
      expect(a.title).toBeTruthy();
      expect(a.image).toMatch(/^images\//);
    }
  });
});
