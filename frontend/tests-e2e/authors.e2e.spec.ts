import { expect, test } from "@playwright/test";

test("authors: global search, clear all, and pagination controls", async ({ page }) => {
  await page.goto("/authors");

  await expect(page.getByRole("heading", { name: "Authors" })).toBeVisible();
  await expect(page.getByTestId("data-table")).toBeVisible();

  const searchInput = page.getByTestId("global-search-input");
  await searchInput.fill("Alice");
  await searchInput.press("Enter");

  await expect(page.locator(".filter-tag.search-tag", { hasText: "Search: Alice" })).toBeVisible();

  await page.getByRole("button", { name: "Clear all filters" }).click();
  await expect(page.locator(".filter-tag.search-tag", { hasText: "Search: Alice" })).toHaveCount(0);

  const pageSizeSelect = page.getByTestId("pagination-size-select");
  await expect(pageSizeSelect).toBeVisible();
  await pageSizeSelect.selectOption("10");

  const nextButton = page.getByTestId("pagination-next");
  if (await nextButton.isEnabled()) {
    await nextButton.click();
    await expect(page.locator(".pagination-page.active", { hasText: "2" })).toBeVisible();
  }
});
