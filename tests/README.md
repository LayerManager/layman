# Layman tests

## Usage
### Run tests in `src` folder
```
make test-src
```

### Run tests in `tests/static_data` folder
```
make test-static
```

### Run other tests in `tests` folder, mainly `dynamic_data` subfolder
```
make test-dynamic
```
Additional parameters for pytest command
- `--nocleanup`: Do not delete publications after tests

Additional parameters for Make command
- `test_type`: Specify level of tests to run
  - Accepted values:
    - `optional`: all tests
    - `mandatory`: only tests marked as `mandatory`
  - Default value is `mandatory`
- `max_fail`: The number of failed test cases after which the program will fail.
  - Accepted values: any non-negative integer
  - Default value is `1`
