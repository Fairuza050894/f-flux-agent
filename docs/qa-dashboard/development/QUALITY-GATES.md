# QA Dashboard Quality Gates

This document defines the required quality gates for Hermes QA Dashboard MVP1.

## Canonical local command

Run from the repository root:

```bash
./venv/bin/python3 scripts/qa_dashboard_quality_gate.py --generate-docs
```

The command performs:

1. Python compilation for `qa_dashboard/backend` and `tests/qa_dashboard`.
2. All QA Dashboard backend tests.
3. Frontend lint.
4. Frontend production build.
5. Documentation synchronization validation.
6. Git whitespace validation.

A change is not ready to commit until the command ends with:

```text
QA DASHBOARD QUALITY GATES PASSED
```

## CI behavior

The workflow `.github/workflows/qa-dashboard-docs.yml` runs the same quality gate for pull requests and pushes affecting the QA Dashboard.

The workflow is deliberately read-only:

- it does not commit generated documentation;
- it does not push changes back to the branch;
- it does not modify the repository description;
- it fails when generated documentation is stale.

Generated documentation must be updated locally and committed with the related product change. This prevents automation-created remote commits from causing branch divergence or `fetch first` push failures.

## Required order

```text
Apply patch
→ Generate documentation
→ Run quality gates
→ Runtime smoke test when applicable
→ Review git diff
→ Commit
→ Fetch and rebase
→ Push
```

## Warning policy

Warnings do not block a build unless the configured tool returns a non-zero exit code. Existing warnings should be recorded as technical debt and must not be confused with successful completion.

## Repository hygiene

Do not use `git add .` for QA Dashboard phases. Stage only the files belonging to the current phase.

The root-level paths below were detected as untracked local prototype files during the P8-D audit and are outside the QA Dashboard scope:

```text
prisma.config.ts
prisma/
src/
```

Do not include them in a QA Dashboard commit unless they are reviewed and intentionally adopted by a separate plan.
