# Testing Improvements Action Plan

## Objective
Ensure the test suite can be executed without external dependencies and covers critical functionality.

## Key Tasks
1. **Isolate External Services**
   - Use pytest fixtures to mock Alpaca API calls, providing deterministic responses.
   - Introduce fake AWS clients or use `moto` to emulate S3 and other AWS services.
2. **Create Test Data**
   - Provide sample market data and account snapshots under `tests/fixtures/`.
   - Use these fixtures across unit and integration tests to avoid hitting live endpoints.
3. **Update Existing Tests**
   - Refactor failing tests to consume mocks and fixtures instead of real credentials.
   - Mark slow or integration-heavy tests so they can be optionally skipped in CI.
4. **Coverage Targets**
   - Aim for at least 80% line coverage across core modules.
   - Add regression tests for the refactored configuration and logging features.
5. **Continuous Integration**
   - Integrate `pytest` into a GitHub Actions workflow running on every pull request.
   - Include linting and coverage reporting as part of the pipeline.

## Deliverables
- Mocked external service fixtures and sample data.
- Updated tests running fully offline.
- CI workflow executing tests and reporting coverage.
- Documentation describing how to run tests locally with mocks.
