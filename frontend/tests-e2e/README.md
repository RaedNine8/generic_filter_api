# Local E2E Tests (Playwright)

## Scope
These tests validate end-to-end user flows for the generic filtering UI using real app behavior in the browser.

## Requirements
1. Backend must be running locally at `http://127.0.0.1:8000`.
2. Run commands from the frontend directory only:
   - `c:/Users/raedn/OneDrive/Bureau/FILES/DEV FILES/PROJECT/filter_test_project/frontend`

## Commands
- Install dependencies: `npm install`
- Install browsers once: `npx playwright install`
- Run tests: `npm run test:e2e`
- Run headed mode: `npm run test:e2e:headed`

## Notes
- Frontend dev server is auto-started by Playwright config.
- Tests use stable `data-testid` selectors to reduce UI-flake risk.
