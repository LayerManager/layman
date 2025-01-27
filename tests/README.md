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


### Run special migration test in `tests/migration_to_v2_0` folder
This test should be run from branch `1048-UUID-master` or from any derived branches. It requires local python 3.8+ available as `python3` executable and appropriate `pip3`. First run takes longer, because it downloads v1.23 docker images and installs python packages in local virtual environment (`.venv` folder). Subsequent runs should be faster,

The test changes Layman version using `git checkout` and it clears current `git stash`. The test tries to keep uncommited changes using `git stash` and `git stash pop`. If you don't want to lose your changes, commit any crucial changes before run.
```bash
./tests/migration_to_v2_0/test.sh
```
