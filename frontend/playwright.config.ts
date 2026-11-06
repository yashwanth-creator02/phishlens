import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:5173";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  use: { baseURL, trace: "on-first-retry" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  // Against a deployed URL pass E2E_BASE_URL; locally the Vite dev server is started for you.
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : { command: "npm run dev", url: baseURL, reuseExistingServer: true, timeout: 60_000 },
});
