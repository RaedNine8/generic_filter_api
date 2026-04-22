import { expect, test } from "@playwright/test";

test("books: suggestion -> filter -> save custom filter -> delete", async ({
  page,
}) => {
  await page.goto("/books");

  await expect(page.getByRole("heading", { name: "Books" })).toBeVisible();
  await expect(page.getByTestId("data-table")).toBeVisible();

  const searchInput = page.getByTestId("global-search-input");
  await searchInput.fill("Alpha");

  const dropdown = page.getByTestId("search-options-dropdown");
  await expect(dropdown).toBeVisible();

  await page
    .getByTestId("search-option")
    .filter({ hasText: "Title" })
    .first()
    .click();

  await expect(page.locator(".filter-tag", { hasText: "Title" })).toBeVisible();

  await page.getByTestId("custom-filters-toggle").click();

  const saveCurrentButton = page.getByTestId("save-current-search");
  await expect(saveCurrentButton).toBeEnabled();
  await saveCurrentButton.click();

  const filterName = `PW Saved ${Date.now()}`;
  await page.locator("#filterName").fill(filterName);
  await page.getByRole("button", { name: "Save", exact: true }).click();

  const savedItem = page
    .getByTestId("saved-filter-item")
    .filter({ hasText: filterName });
  await expect(savedItem).toBeVisible();

  page.once("dialog", (dialog) => dialog.accept());
  await savedItem.getByTestId("saved-filter-delete").click();

  await expect(
    page.getByTestId("saved-filter-item").filter({ hasText: filterName }),
  ).toHaveCount(0);
});

test("books: advanced custom builder, relation search, no-results, sort state, and retry", async ({
  page,
}) => {
  test.setTimeout(90_000);

  const openCustomFiltersPanel = async () => {
    const toggle = page.getByTestId("custom-filters-toggle");
    const expanded = await toggle.getAttribute("aria-expanded");
    if (expanded !== "true") {
      await toggle.click();
    }
  };

  const closeCustomFiltersPanel = async () => {
    const toggle = page.getByTestId("custom-filters-toggle");
    const expanded = await toggle.getAttribute("aria-expanded");
    if (expanded === "true") {
      await toggle.click();
    }
  };

  await page.goto("/books");

  await expect(page.getByRole("heading", { name: "Books" })).toBeVisible();
  await expect(page.getByTestId("data-table")).toBeVisible();

  const searchInput = page.getByTestId("global-search-input");

  await searchInput.fill("Alpha");
  const dropdown = page.getByTestId("search-options-dropdown");
  await expect(dropdown).toBeVisible();

  const disabledOption = page
    .getByTestId("search-option")
    .filter({ hasText: "enter a number" })
    .first();
  await expect(disabledOption).toHaveClass(/disabled/);

  const disabledBooleanOption = page
    .getByTestId("search-option")
    .filter({ hasText: "enter true/false" })
    .first();
  await expect(disabledBooleanOption).toHaveClass(/disabled/);

  const currentAdvancedTagCount = await page
    .locator(".filter-tag.advanced-tag")
    .count();
  await disabledOption.click();
  await expect(page.locator(".filter-tag.advanced-tag")).toHaveCount(
    currentAdvancedTagCount,
  );

  await searchInput.fill("Alpha");
  await expect(page.getByTestId("search-options-dropdown")).toBeVisible();

  const firstActiveOption = page
    .locator(".search-option:not(.custom-filter-option):not(.disabled)")
    .first();
  await firstActiveOption.click();

  await expect(page.locator(".filter-tag.advanced-tag")).toHaveCount(
    currentAdvancedTagCount + 1,
  );

  await openCustomFiltersPanel();
  await page.getByRole("button", { name: "New custom filter" }).click();

  await expect(
    page.getByRole("heading", { name: "Custom Filter Builder" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Apply Filters" }).click();

  await expect(page.locator(".filter-tag.advanced-tag")).toHaveCount(
    currentAdvancedTagCount + 1,
  );

  await openCustomFiltersPanel();
  await page.getByRole("button", { name: "New custom filter" }).click();
  await page
    .locator(".filter-builder-modal")
    .locator("button", { hasText: "Clear All" })
    .click();
  await expect(page.locator(".filter-tag.advanced-tag")).toHaveCount(0);

  await searchInput.fill("Alice");
  await expect(page.getByTestId("search-options-dropdown")).toBeVisible();

  const relationOption = page
    .locator(".search-option:has(.option-type)")
    .filter({ hasText: "Relation" })
    .first();
  await relationOption.click();

  await expect(page.locator(".filter-tag.advanced-tag")).toHaveCount(1);

  await searchInput.fill("zzzz_no_hit_12345");
  await searchInput.press("Enter");
  await expect(
    page.locator(".empty-message", {
      hasText: "No matches for current criteria",
    }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Clear all filters" }).click();
  await expect(
    page.locator(".empty-message", {
      hasText: "No matches for current criteria",
    }),
  ).toHaveCount(0);
  await expect(page.locator(".context-pill.result-pill")).toContainText(
    /\d+ results/,
  );

  await closeCustomFiltersPanel();

  const titleSortButton = page
    .getByTestId("data-table")
    .getByRole("button", { name: "Title" });
  await titleSortButton.click();
  await expect(
    page.locator(".context-pill", { hasText: "Sorted: Title (Asc)" }),
  ).toBeVisible();

  await titleSortButton.click();
  await expect(
    page.locator(".context-pill", { hasText: "Sorted: Title (Desc)" }),
  ).toBeVisible();

  let failNextBooksList = true;
  await page.route("**/api/books**", async (route) => {
    const requestUrl = new URL(route.request().url());
    if (failNextBooksList && requestUrl.pathname === "/api/books") {
      failNextBooksList = false;
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Forced test failure" }),
      });
      return;
    }

    await route.continue();
  });

  await page.reload();
  await expect(page.getByText("Could not load data.")).toBeVisible();
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByText("Could not load data.")).toHaveCount(0);
  await expect(page.getByTestId("data-table")).toBeVisible();

  await page.unroute("**/api/books**");
});
