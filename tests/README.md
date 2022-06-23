# Layman tests

With increasing complexity and funcionality of Layman, number of tests using Layman's REST API also grew. This led to complicated searchability as it was not clear which tests belongs to which functionality. It also led to many time consuming tests as each such test required new publication to be published, which takes about 5s per publication.

We decided to structure tests according to simple decision tree introduced below. Our goal was better searchability of current tests and also better options of optimization to decrease tests duration.

## Usage
### Run tests in `src` folder
```
make test
```
### Run tests in `tests` folder
```
make test-separated
```
Additional parameters for pytest command line
- `--nocleanup`: Do not delete publications after tests

Additional environment setting for pytest command line
- `TEST_TYPE`: Specify level of tests to run 
  - Accepted values: `optional`/`mandatory`
  - Default value is `mandatory`

## Rules
- Every direct subfolder of `tests`, e.g. `static_data` or `failed_publications`, relies on that tests from other folders will not use their workspaces.
- Each test in `tests` and `src` takes into account that other workspaces may be created in parallel. Also, in such other workspaces, publications can be created and deleted in parallel.
- Tests in `tests/static_data` do not change tested data defined in `tests/static_data/__init__.py` (users, workspaces, publications). These tests can also share tested data among them and they are able to run in parallel with other tests in `tests/static_data`.
- Tests in `tests/static_data/multi_publications` are testing only multi-publication endpoints. Tests in `tests/static_data/single_publication` are testing only single-publication endpoints.

## Recommendations
- For each test in `tests/static_data`, ensure that at least one combination of testing data exists in `tests/static_data/__init__.py::PUBLICATIONS`. It should be done by `assert` in `tests/static_data/__init__.py`.

## Test placement
We expect to change this decision tree over time.
- Is it test of upgrade/migration?
  - YES: It belongs to `tests/upgrade`.
- Is the test without `ensure_layman*` fixtures and methods?
  - YES: It belongs to `src`.
- Is the test restarting Layman or running Layman with non-default environment variables?
  - YES: It belongs to `tests/restart`.
- Is the test independent on data in Layman (e.g. users, workspaces, or publications)?
  - YES: It belongs to `tests/immputable_endpoints`.
- Is the test testing workspaces or users?
  - YES: It belongs to `tests/users_and_workspaces`.
- Is the test testing errors of publication endpoints, including errors in asynchronous tasks?
  - YES: It belongs to `tests/failed_publications`.
- Is the test testing state before and after publication-related action, e.g. PATCH Layer or WFS-T, or during asynchronous task?
  - YES: It belongs to `tests/dynamic_data`.
- Is the test testing multiple publication endpoints?
  - YES: It belongs to `tests/static_data/multi_publications`.
- Otherwise: It belongs to `tests/static_data/single_publications`.
