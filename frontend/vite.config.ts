import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// In development the API runs on :8000; the proxy avoids CORS and keeps URLs identical to production (nginx).
// VITE_DEV_API_TARGET points the proxy somewhere else when :8000 is taken (a stale process, a container).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_DEV_API_TARGET || "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  test: { environment: "jsdom", setupFiles: "./src/test/setup.ts", include: ["src/**/*.test.{ts,tsx}"] },
});
