# Frontend customization and safe updates

This is implemented for **Angular, React/Vite, Next.js and Vue**. It is not an Angular-only feature.

## Ownership model

| Layer             | Contents                                                              | Update behavior                                                                                                                                          |
| ----------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| User-owned        | Shell component, theme CSS, presentation JSON; Next.js host page      | Created once. Existing content is preserved byte-for-byte.                                                                                               |
| Generated schema  | Entity types/configs, Angular entity pages/routes, display projection | Regenerated from scan/IR; obsolete tracked generated files are pruned only when unmodified.                                                              |
| Generated runtime | API client, filter/query/export logic, reusable widgets               | Independent of entity schema. Unchanged output is not rewritten. A CLI/runtime upgrade may change it, but only against an unmodified installed baseline. |
| Host integration  | Routes, providers, dependency wiring                                  | Narrow reconciliation; preserve unrelated code and existing dependency versions. Angular managed route blocks have separate edit protection.             |

The implementation is shared in `filterx/core/frontend_lifecycle.py`. The manifest stores installed hashes; `.filterx/frontend-<framework>.json` records schema and ownership. Keep both in version control alongside generated source. They are not disposable cache if you want safe update history.

Angular's runtime still lives under `src/app/core`, `src/app/shared`, and the installed global stylesheet for compatibility. Being outside `filterx-generated` does **not** make those copied runtime files user-owned. Use the diagnostic file list to identify ownership.

## Customization locations

Paths below are relative to the configured frontend workspace:

| Frontend   | Create-once shell                                   | Additional user-owned files                                  |
| ---------- | --------------------------------------------------- | ------------------------------------------------------------ |
| Angular    | `src/app/filterx-custom/filterx-shell.component.ts` | `theme.css`, `presentation.json` in the same folder          |
| React/Vite | `src/filterx-custom/FilterxShell.tsx`               | Same                                                         |
| Next.js    | `src/filterx-custom/FilterxShell.tsx`               | Same, plus the initial host route `src/app/filterx/page.tsx` |
| Vue        | `src/filterx-custom/FilterxShell.vue`               | Same                                                         |

Set `frontend.customization_root` to a **project-relative** path to choose another location before the first install. Web generated paths remain relative to their target workspace, while Angular's `frontend.generated_root` remains project-relative. Generated/custom trees must not overlap. After installation, changing these roots is blocked: first plan an explicit import/layout migration, because user-owned shells are not silently rewritten.

### Display settings shared across all frameworks

Edit the create-once `presentation.json`:

```json
{
  "Book": {
    "label": "Our library",
    "columns": ["title", "rating"],
    "labels": { "title": "Book title", "rating": "Reader rating" }
  }
}
```

- Keys are model/entity names and backend field names, **not** the displayed labels.
- Supported options are `label`, `columns`, and `labels` only.
- Omitting `columns` uses generated defaults; an empty list deliberately displays no columns.
- Unknown/removed entities and fields are reported and excluded from the generated display projection. Your JSON is preserved so you can repair it deliberately.
- Invalid JSON/types or attempted query overrides such as `apiEndpoint` block generation.
- Run `frontend install` after presentation edits to refresh the generated display projection, then rebuild/reload the host. JSON is not fetched live by the browser.
- Presentation is not access control. Backend permission hooks, row predicates, field visibility, cost limits and export checks remain authoritative.

### Angular

Customize the shell's template/layout or its `theme.css`; generated entity pages import this stable shell instead of owning the customized view.

The shell retains `config`, `copilotEnabled`, `showHeader`, `description`, `clickableRows`, and `onRowClicked` inputs. It applies display settings without changing the entity name, API endpoint, query defaults or filter field identifiers.

For a host-owned page, use `[filterxHeader]`/`[filterxFooter]` content projection and a `#cellTemplate` or explicit `cellTemplate` input. Cell template context is `$implicit` (value), `row`, and `column`. To retain the core controls, customize the wrapper around `app-entity-list` rather than replacing its query implementation. Style inherited CSS variables from the shell or add your own host stylesheet after the installed global styles.

### React/Vite and Next.js

The shell forwards typed `FilterxAppProps` to the managed app. Supply or edit these render props in your shell:

- `renderHeader(context)`
- `renderToolbar(context)`
- `renderCell(context)`

Context includes entity metadata, rows, query state, pagination metadata, grouping results, loading/error state and `refresh()`. Cell context adds `row`, `rowIndex`, `field`, and `value`. Render labels differently, but use `field.name` for queries. Header/toolbar/cell rendering does not replace filtering, sorting, pagination, grouping or export implementation.

Keep Next.js's `'use client'` directive on the shell. Its initial route can remain a server component importing that client shell. Define callback render props within a client component, not as functions passed across the server/client boundary. Existing custom Next pages without a recognized FilterX import are preserved and produce a mount warning instead of being replaced.

### Vue

The shell exposes typed `header`, `toolbar`, and `cell` slots with the same contexts as the React render props. Customize those slots or edit the user-owned shell's layout. The managed query implementation stays behind `FilterxApp`. For example, a cell slot can render `value` as a badge while `field.name` remains the query key. The shell imports the user-owned theme after the runtime's scoped `.fx-*` styles.

## Model, field and relationship updates

1. Commit or otherwise back up your working tree. Apply your application's own ORM/database migrations; FilterX does not migrate domain tables for you.
2. Run `filterx scan --project-root . --config filterx.yaml --no-dry-run --json`.
3. Run `filterx frontend diff --project-root . --config filterx.yaml --json` to inspect proposed file changes and unified diffs.
4. Run `filterx frontend doctor --project-root . --config filterx.yaml --json` to inspect conflicts, preserved files, layout and schema changes. Add `--fail-on-warning` for stricter automation.
5. Run `filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json` to synchronize the enabled backend, agent and frontend layers.
6. Run `filterx validate`, then the host's dependency install (if needed), build and integration tests. Restart/reload backend processes so agent metadata and endpoints use the current generation.

Both diagnostics are **read-only even if `--no-dry-run` is supplied**. They compare against existing scan/IR artifacts, not the live database. A fresh scan is essential. `doctor` is an update-readiness report, not a replacement for a TypeScript build or backend runtime test.

Reports include added/removed entities, changed fields/types/operations, changed relationships and table mappings. Removal/change is conservatively marked `breaking`. Renames appear as removal plus addition; the tool does not guess a data migration. The all-in-one installer preflights the frontend after scanning and before writing backend/agent/database integrations. The scan itself may write metadata artifacts; the multi-layer installer is not a database/filesystem transaction.

## Conflicts and recovery

- A managed file differing from its installed hash blocks the entire frontend apply before any source writes or deletions. `--force` does not bypass this. Move your UI changes into user-owned files, restore the corresponding managed baseline from Git/backup, review the diff, then reinstall.
- First installs do not overwrite differing untracked files at generated paths. Choose noncolliding paths or explicitly reconcile the existing files.
- An unchanged legacy installation can migrate using its existing manifest hashes. Edited legacy Angular routes without block-level history conservatively block migration; review/restore the route file before retrying. There is no automatic three-way source merge.
- Normal upgrades preserve host routes outside the generated block. Changes inside the block, such as a guard added manually, block regeneration rather than silently disappearing. Put long-lived custom routes/guards in host-owned routes.
- Legacy files without recorded frontend ownership are not broadly pruned just because they sit in a generated directory. Review leftovers manually; arbitrary directory deletion would risk user code.
- New frontend patch bundles check every affected file before rollback. Later shell/theme/host edits cause rollback to refuse before restoring anything. Back up/merge those edits and roll back in reverse order using explicit patch IDs. Old bundles predating this feature do not gain these guards retroactively.

## Guarantee boundaries

This feature guarantees **preservation or an explicit conflict**, not that every arbitrary customization works against every future schema/API version. A custom renderer referencing a removed field, an existing saved filter, a changed backend hook, or a framework major-version incompatibility may require manual updates. Templates and TypeScript builds help detect those issues; schema diff does not rewrite custom business logic or saved filters. Hiding a column in presentation never grants or revokes backend access.

Recommended regression checks: customize a shell and theme; rename/add/remove a field and relationship; regenerate; verify custom bytes remain unchanged, runtime timestamps stay unchanged for schema-only changes, diagnostics identify breaking changes, filters/exports still use raw backend keys, and edited managed files block both normal and stale-file writes.
