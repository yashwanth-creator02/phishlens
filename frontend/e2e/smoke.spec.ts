import { expect, test } from "@playwright/test";

// Works in both auth modes: Supabase configured (sign-in form) and disabled (notice).
test("login route renders in either auth mode", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: /sign in|authentication disabled/i })).toBeVisible();
});

const email = process.env.E2E_EMAIL;
const password = process.env.E2E_PASSWORD;

test.describe("signed-in smoke", () => {
  test.skip(!email || !password, "Set E2E_EMAIL and E2E_PASSWORD to run the signed-in smoke test.");

  test("core pages render for a signed-in analyst", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email address").fill(email!);
    // exact, because the reveal toggle next to it is labelled "Show password".
    await page.getByLabel("Password", { exact: true }).fill(password!);
    await page.getByRole("button", { name: "Sign in" }).click();

    // The sign-in request has to finish and persist the session before the page is reloaded,
    // otherwise the reload drops the half-written session and the guard bounces to /login.
    await expect(page.getByRole("heading", { level: 1, name: /Triage dashboard/ })).toBeVisible();

    const routes = [
      ["/", /Triage dashboard/],
      ["/history", /^History$/],
      ["/model", /Model card/],
      ["/how-it-works", /How it works/],
      ["/profile", /^Profile$/],
      ["/status", /^Status$/],
    ] as const;

    for (const [path, heading] of routes) {
      await page.goto(path);
      await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
    }
  });
});
