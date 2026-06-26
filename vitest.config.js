import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // storage.js / app.js は window と localStorage を使うため jsdom 環境で実行
    environment: "jsdom",
    include: ["tests/**/*.test.js"],
    globals: true,
  },
});
