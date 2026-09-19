# FilterX legacy golden outputs

The original six snapshots remain authoritative for scan and backend generation.
The customizable frontend intentionally changes wrapper pages, runtime template
extension points, ownership state, diagnostics and guarded rollback metadata.
`frontend_v2_digests.json` records SHA-256 hashes of the complete normalized
`capture_scenario` results for this new lifecycle, avoiding another copy of the
large backend/runtime snapshots. Tests compare original scan/backend output
exactly and compare the full new lifecycle digest; changed hashes require an
explicit file/command difference audit, not an automatic acceptance.

These snapshots capture the current pre-refactor behavior required by Section 0 and Step 1 of `filterx-multibackend-spec.md`.

Covered scenarios:

- simple entity
- one-to-many relationship
- many-to-many relationship
- relationship cycle
- configured soft-delete behavior
- custom global predicate hook

Each snapshot records the observable output of scan, backend install, frontend install, database install, idempotent reinstall, and reverse-order rollback. It includes generated files, host-file mutations, manifest v1 state, patch metadata, and backups.

Normalization is intentionally limited to values that cannot be stable between runs:

- absolute fixture root → `<PROJECT_ROOT>`
- generated patch IDs → ordered `<PATCH_NNN>` values
- UTC creation/update timestamps → `<TIMESTAMP>`
- Windows path separators → `/`

Content hashes are not normalized because they are part of the compatibility contract. Update these files only when a generated-output difference is intentional and explicitly approved.

To recapture with the repository virtual environment:

    .venv/Scripts/python.exe tools/filterx/tests/capture_golden.py
