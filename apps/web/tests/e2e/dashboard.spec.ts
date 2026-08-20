import { expect, test } from "@playwright/test";

test("demo user reaches the research dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: /One-click demo login/i }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(
    page.getByRole("heading", { name: /Market overview/i }),
  ).toBeVisible();
  await expect(
    page.getByText(/For education and research only/i).first(),
  ).toBeVisible();

  if (process.env.CAPTURE_SCREENSHOT === "true") {
    await page.screenshot({
      path: "../../docs/screenshots/dashboard.png",
      fullPage: true,
    });
  }
});
