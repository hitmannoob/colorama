# Migrating colorama's tests from unittest to pytest

## Baseline before migration

The project's unittest runner (as used by `tox.ini` and the `Makefile`) is run
from the repository root:

```
python -m unittest discover -p '*_test.py'
```

Result on the pre-migration tree:

```
Ran 52 tests in 0.009s

OK (skipped=14)
```

So the baseline is **52 tests** (38 run, 14 skipped because they are
Windows-only or require a TTY).

Note: `python -m unittest discover -s colorama/tests -p '*_test.py'` does *not*
work for this project: the test modules use package-relative imports
(`from ..ansi import ...`) and fail with `ImportError: attempted relative import
with no known parent package` when discovery is rooted inside the package. The
tox/Makefile command above is the authoritative one.

## Target

`python -m pytest` must collect at least 52 tests. Configuration lives in
`[tool.pytest.ini_options]` in `pyproject.toml`, which points pytest at
`colorama/tests` and collects `*_test.py` files.
