# CI Pipeline Guide (GitHub Actions)

This repository now uses a pyramidal test strategy:

- **Unit tests (majority):** fast, isolated tests for algorithms and helper mechanisms.
- **Integration tests (smaller set):** test multi-function flows (for example persistence pipeline behavior).
- **UI/outside API are excluded from this test scope.**

## 1) What was added

- Workflow: `/home/runner/work/DSWingSpot/DSWingSpot/.github/workflows/ci.yml`
- Test folders:
  - `/home/runner/work/DSWingSpot/DSWingSpot/tests/unit`
  - `/home/runner/work/DSWingSpot/DSWingSpot/tests/integration`
- Coverage config: `/home/runner/work/DSWingSpot/DSWingSpot/.coveragerc`
- Pytest config: `/home/runner/work/DSWingSpot/DSWingSpot/pytest.ini`

## 2) Coverage target and measurement

Coverage is enforced with `fail_under = 70` in `.coveragerc`.

Run locally:

```bash
pytest --cov --cov-report=term-missing --cov-report=xml
```

The workflow runs the same command and will fail if total coverage drops below 70%.

## 3) How to configure GitHub CI services

1. Push the workflow file to your repository default branch.
2. Open GitHub repository **Settings → Actions → General**.
3. Ensure Actions are enabled:
   - **Allow all actions and reusable workflows** (or allow GitHub-authored actions at minimum).
4. In **Workflow permissions**, keep at least **Read repository contents**.
5. Create or update branch protection rules (recommended):
   - **Settings → Branches → Add rule** for your protected branch.
   - Enable **Require status checks to pass before merging**.
   - Select the workflow job check: `unit-and-integration-tests`.
6. Optional quality gates:
   - Require pull request reviews.
   - Require branch up-to-date before merge.
   - Restrict direct pushes to protected branches.

## 4) Pipeline stages in GitHub Actions

1. **Checkout** repository.
2. **Setup Python 3.12**.
3. **Install test dependencies** needed by mechanism tests.
4. **Run test pyramid + coverage gate**.
5. **Upload `coverage.xml` artifact** for later analysis or external reporting.

## 5) Extending the pipeline

- Add additional integration tests under `tests/integration` for cross-module behavior.
- Add end-to-end tests only for critical user paths and keep them a minority of the suite.
- If you later introduce external coverage services (Codecov/Coveralls), consume `coverage.xml` from CI artifacts.
- Keep algorithm-level tests isolated with mocks/fixtures to preserve fast feedback.

## 6) Troubleshooting CI failures

- **Import errors:** verify `tests/conftest.py` path bootstrap remains intact.
- **Coverage below threshold:** add tests for changed mechanism modules before merging.
- **Dependency issues:** keep CI dependency install list aligned with test imports.
