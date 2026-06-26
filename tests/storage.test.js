import { beforeEach, describe, expect, it } from "vitest";

// 実コードはモジュールではなく window に公開するスクリプト。
// jsdom 環境で side-effect import すると window.STAMP_CONFIG / window.StampStore が設定される。
import "../js/config.js";
import "../js/storage.js";

const Store = window.StampStore;
const CFG = window.STAMP_CONFIG;

beforeEach(() => {
  // 各テストを独立させるため毎回ストレージを空にする
  localStorage.clear();
});

describe("StampStore.isAvailable", () => {
  it("jsdom 環境では true を返す", () => {
    expect(Store.isAvailable()).toBe(true);
  });
});

describe("StampStore.getParticipantId", () => {
  it("P-... 形式のIDを生成する", () => {
    const id = Store.getParticipantId();
    expect(id).toMatch(/^P-[0-9a-z]+-[0-9a-z]{1,6}$/);
  });

  it("2回呼んでも同じIDを返す（永続化される）", () => {
    const a = Store.getParticipantId();
    const b = Store.getParticipantId();
    expect(b).toBe(a);
  });
});

describe("StampStore.getStamps", () => {
  it("初期状態では空オブジェクトを返す", () => {
    expect(Store.getStamps()).toEqual({});
  });

  it("壊れたJSONが入っていても例外を出さず {} を返す", () => {
    localStorage.setItem(CFG.storagePrefix + "stamps", "{壊れたJSON");
    expect(Store.getStamps()).toEqual({});
  });

  it("配列など object でない値が入っていても {} を返す", () => {
    localStorage.setItem(CFG.storagePrefix + "stamps", "123");
    expect(Store.getStamps()).toEqual({});
  });
});

describe("StampStore.ensureInitialized", () => {
  it("未初期化なら空オブジェクトで初期化する", () => {
    expect(localStorage.getItem(CFG.storagePrefix + "stamps")).toBeNull();
    Store.ensureInitialized();
    expect(localStorage.getItem(CFG.storagePrefix + "stamps")).toBe("{}");
  });

  it("既存データを上書きしない", () => {
    Store.addStamp("A1");
    Store.ensureInitialized();
    expect(Store.hasStamp("A1")).toBe(true);
  });
});

describe("StampStore.addStamp", () => {
  it("初回追加は true を返し、保存される", () => {
    expect(Store.addStamp("A1")).toBe(true);
    expect(Store.hasStamp("A1")).toBe(true);
  });

  it("同じエリアの2回目の追加は false を返す（重複防止）", () => {
    expect(Store.addStamp("A1")).toBe(true);
    expect(Store.addStamp("A1")).toBe(false);
  });

  it("重複追加で枚数は増えない", () => {
    Store.addStamp("A1");
    Store.addStamp("A1");
    expect(Store.count()).toBe(1);
  });

  it("取得時刻(ms)が記録される", () => {
    const before = Date.now();
    Store.addStamp("A1");
    const ts = Store.getStamps()["A1"];
    expect(typeof ts).toBe("number");
    expect(ts).toBeGreaterThanOrEqual(before);
  });
});

describe("StampStore.count / hasStamp", () => {
  it("異なるエリアを追加すると枚数が増える", () => {
    Store.addStamp("A1");
    Store.addStamp("A2");
    Store.addStamp("A3");
    expect(Store.count()).toBe(3);
  });

  it("未取得エリアは hasStamp が false", () => {
    expect(Store.hasStamp("A9")).toBe(false);
  });
});

describe("StampStore.resetAll", () => {
  it("全スタンプを消去して空に戻す", () => {
    Store.addStamp("A1");
    Store.addStamp("A2");
    Store.resetAll();
    expect(Store.count()).toBe(0);
    expect(Store.getStamps()).toEqual({});
  });
});

describe("クリア／コンプリート判定（stamp.js・app.js と同じ閾値ロジック）", () => {
  const codes = CFG.areas.map((a) => a.code);

  it("clearThreshold 未満は未クリア", () => {
    for (let i = 0; i < CFG.clearThreshold - 1; i++) Store.addStamp(codes[i]);
    expect(Store.count() >= CFG.clearThreshold).toBe(false);
  });

  it("clearThreshold 個でクリア成立", () => {
    for (let i = 0; i < CFG.clearThreshold; i++) Store.addStamp(codes[i]);
    expect(Store.count() >= CFG.clearThreshold).toBe(true);
    expect(Store.count() >= CFG.totalStamps).toBe(false);
  });

  it("全エリアでコンプリート成立", () => {
    codes.forEach((c) => Store.addStamp(c));
    expect(Store.count() >= CFG.totalStamps).toBe(true);
  });
});
