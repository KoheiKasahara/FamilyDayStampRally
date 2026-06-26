// 実コードはモジュールではなく window に公開するスクリプト。
// Node 単体（npm 不要）で動かすため、window と localStorage を最小実装して読み込む。
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..", "..");

class MemoryStorage {
  constructor() {
    this.m = new Map();
  }
  getItem(k) {
    return this.m.has(k) ? this.m.get(k) : null;
  }
  setItem(k, v) {
    this.m.set(k, String(v));
  }
  removeItem(k) {
    this.m.delete(k);
  }
  clear() {
    this.m.clear();
  }
}

// js/config.js → js/storage.js の順に評価し、StampStore / STAMP_CONFIG を取り出す
export function loadApp() {
  const win = {};
  win.localStorage = new MemoryStorage();
  globalThis.window = win;
  globalThis.localStorage = win.localStorage;

  const run = (rel) => (0, eval)(fs.readFileSync(path.join(ROOT, rel), "utf8"));
  run("js/config.js");
  run("js/storage.js");

  return {
    Store: win.StampStore,
    CFG: win.STAMP_CONFIG,
    localStorage: win.localStorage,
  };
}
