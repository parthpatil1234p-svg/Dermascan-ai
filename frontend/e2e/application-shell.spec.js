import { expect, test } from "@playwright/test";

test("home exposes the project and final safety disclaimer", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /understand your skin/i })).toBeVisible();
  await expect(page.getByText(/does not prescribe treatment/i).first()).toBeVisible();
});

test("unauthenticated direct workflow access returns to login", async ({ page }) => {
  await page.goto("/final-report");
  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByRole("heading", { name: /login to dermascan ai/i }),
  ).toBeVisible();
});

test("login validation blocks malformed input without an API request", async ({ page }) => {
  let loginRequests = 0;
  page.on("request", (request) => {
    if (request.url().includes("/api/auth/login")) loginRequests += 1;
  });
  await page.goto("/login");
  await page.getByLabel("Email address").fill("not-an-email");
  await page.getByLabel("Password", { exact: true }).fill("short");
  await page.getByRole("button", { name: /^login$/i }).click();
  await expect(page.getByText(/valid email address/i)).toBeVisible();
  expect(loginRequests).toBe(0);
});

test("main pages do not create horizontal viewport overflow", async ({ page }) => {
  for (const path of ["/", "/login", "/register", "/products", "/ingredients"]) {
    await page.goto(path);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    );
    expect(overflow, `${path} should fit the viewport`).toBe(false);
  }
});
