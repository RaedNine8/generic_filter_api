import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests-e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  expect: {
    timeout: 10_000,
  },
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:4200",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: "npm run start -- --host 127.0.0.1 --port 4200",
    url: "http://127.0.0.1:4200",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
