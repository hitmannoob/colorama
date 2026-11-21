#!/usr/bin/env bash
# Install pytest and this package, then run the test suite.
set -euo pipefail

python -m pip install -q pytest -e .
python -m pytest -q
