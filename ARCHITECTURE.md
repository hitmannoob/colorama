# Architecture

This document records how the test suite is organised and the decisions behind
moving it from `unittest` to `pytest`. It complements `MIGRATION.md`, which holds
the baseline collected-test count.

## Package layout

- `colorama/` – the library itself. **Unchanged by the test migration.** Code
  outside `colorama/tests/` must not be modified.
- `colorama/tests/` – the test suite. One module per area under test:
  - `ansi_test.py`
  - `ansitowin32_test.py`
  - `initialise_test.py`
  - `isatty_test.py`
  - `winterm_test.py`
- `colorama/tests/conftest.py` – shared pytest fixtures (formerly the helper
  functions/classes in `colorama/tests/utils.py`).

## Test style

The suite uses pytest idioms throughout:

- Plain `assert` statements instead of `self.assert*` methods.
- pytest fixtures instead of `setUp`/`tearDown` and `unittest.mock.patch`
  decorators where a fixture reads more clearly.
- `pytest.mark.parametrize` where the same check runs over many inputs.
- `pytest.mark.skipif` (or an equivalent platform guard) instead of
  `unittest.skipUnless`. Windows-only behaviour stays skipped on other
  platforms exactly as before.

No test class inherits from `unittest.TestCase` and no test calls
`self.assert*`.

## Shared helpers

Helpers that several test modules need live in `colorama/tests/conftest.py` and
are exposed as fixtures so pytest can inject them:

- stream stand-ins (`StreamTTY`, `StreamNonTTY`),
- `osname` – temporarily override `os.name`,
- `replace_by` / `replace_original_by` – temporarily swap `sys.stdout` /
  `sys.stderr` (and their `__std*__` originals),
- `pycharm` – emulate running under PyCharm via `PYCHARM_HOSTED`.

Because fixtures cannot be imported like ordinary functions, any remaining
non-fixture helpers are defined directly in `conftest.py` or duplicated locally
where a module is the only user. `utils.py` is retired once every module has
migrated.

## Running the tests

```sh
pip install -q pytest -e .
python -m pytest
```

`check.sh` at the repository root performs exactly this install-and-run step.
`tox`, the `Makefile` `test` target, `requirements-dev.txt` and the PowerShell
helpers all invoke `pytest` as well.

## Configuration

pytest is configured under `[tool.pytest.ini_options]` in `pyproject.toml` so a
bare `python -m pytest` from the repository root discovers
`colorama/tests/`. The suite is self-contained and does not need a database or
network access.

## Invariants

1. `python -m pytest` passes.
2. pytest collects **at least** the number of tests recorded in `MIGRATION.md`
   for the old unittest runner. Parametrisation may make the collected count
   higher; it must never be lower.
3. No `unittest.TestCase` subclasses and no `self.assert*` calls remain in
   `colorama/tests/`.
4. Files under `colorama/` outside `colorama/tests/` are byte-for-byte
   unchanged by the migration.
