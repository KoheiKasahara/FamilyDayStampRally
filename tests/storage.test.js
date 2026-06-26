// Node 内蔵テストランナーで実行（インストール不要）:  node --test
import { describe, it, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { loadApp } from "./helpers/load-app.js";

const { Store, CFG, localStorage } = loadApp();

beforeEach(() => {
  // 各テストを独立させるため毎回ストレージを空にする
  localStorage.clear();
});

describe("StampStore.isAvailable", () => {
  it("利用可能なら true を返す", () => {
    assert.equal(Store.isAvailable(), true);
  });
});

describe("StampStore.getParticipantId", () => {
  it("P-... 形式のIDを生成する", () => {
    assert.match(Store.getParticipantId(), /^P-[0-9a-z]+-[0-9a-z]{1,6}$/);
  });

  it("2回呼んでも同じIDを返す（永続化される）", () => {
    const a = Store.getParticipantId();
    const b = Store.getParticipantId();
    assert.equal(b, a);
  });
});

describe("StampStore.getStamps", () => {
  it("初期状態では空オブジェクトを返す", () => {
    assert.deepEqual(Store.getStamps(), {});
  });

  it("壊れたJSONが入っていても例外を出さず {} を返す", () => {
    localStorage.setItem(CFG.storagePrefix + "stamps", "{壊れたJSON");
    assert.deepEqual(Store.getStamps(), {});
  });

  it("object でない値が入っていても {} を返す", () => {
    localStorage.setItem(CFG.storagePrefix + "stamps", "123");
    assert.deepEqual(Store.getStamps(), {});
  });
});

describe("StampStore.ensureInitialized", () => {
  it("未初期化なら空オブジェクトで初期化する", () => {
    assert.equal(localStorage.getItem(CFG.storagePrefix + "stamps"), null);
    Store.ensureInitialized();
    assert.equal(localStorage.getItem(CFG.storagePrefix + "stamps"), "{}");
  });

  it("既存データを上書きしない", () => {
    Store.addStamp("A1");
    Store.ensureInitialized();
    assert.equal(Store.hasStamp("A1"), true);
  });
});

describe("StampStore.addStamp", () => {
  it("初回追加は true を返し、保存される", () => {
    assert.equal(Store.addStamp("A1"), true);
    assert.equal(Store.hasStamp("A1"), true);
  });

  it("同じエリアの2回目の追加は false を返す（重複防止）", () => {
    assert.equal(Store.addStamp("A1"), true);
    assert.equal(Store.addStamp("A1"), false);
  });

  it("重複追加で枚数は増えない", () => {
    Store.addStamp("A1");
    Store.addStamp("A1");
    assert.equal(Store.count(), 1);
  });

  it("取得時刻(ms)が記録される", () => {
    const before = Date.now();
    Store.addStamp("A1");
    const ts = Store.getStamps()["A1"];
    assert.equal(typeof ts, "number");
    assert.ok(ts >= before);
  });
});

describe("StampStore.count / hasStamp", () => {
  it("異なるエリアを追加すると枚数が増える", () => {
    Store.addStamp("A1");
    Store.addStamp("A2");
    Store.addStamp("A3");
    assert.equal(Store.count(), 3);
  });

  it("未取得エリアは hasStamp が false", () => {
    assert.equal(Store.hasStamp("A9"), false);
  });
});

describe("StampStore.resetAll", () => {
  it("全スタンプを消去して空に戻す", () => {
    Store.addStamp("A1");
    Store.addStamp("A2");
    Store.resetAll();
    assert.equal(Store.count(), 0);
    assert.deepEqual(Store.getStamps(), {});
  });
});

describe("クリア／コンプリート判定（stamp.js・app.js と同じ閾値ロジック）", () => {
  const codes = CFG.areas.map((a) => a.code);

  it("clearThreshold 未満は未クリア", () => {
    for (let i = 0; i < CFG.clearThreshold - 1; i++) Store.addStamp(codes[i]);
    assert.equal(Store.count() >= CFG.clearThreshold, false);
  });

  it("clearThreshold 個でクリア成立", () => {
    for (let i = 0; i < CFG.clearThreshold; i++) Store.addStamp(codes[i]);
    assert.equal(Store.count() >= CFG.clearThreshold, true);
    assert.equal(Store.count() >= CFG.totalStamps, false);
  });

  it("全エリアでコンプリート成立", () => {
    codes.forEach((c) => Store.addStamp(c));
    assert.equal(Store.count() >= CFG.totalStamps, true);
  });
});
