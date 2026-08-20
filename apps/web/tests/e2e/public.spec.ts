import { expect, test } from "@playwright/test";

test("landing and methodology are useful without authentication", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /See the signal/i }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: /Read the complete methodology/i })
    .click();
  await expect(
    page.getByRole("heading", { name: /Transparent enough/i }),
  ).toBeVisible();
});
