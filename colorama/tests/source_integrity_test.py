"""Guard that the migration only touched code under ``colorama/tests/``.

The sha256 digests below are the contents of the non-test modules at the
pre-migration commit (0496145). Acceptance criterion 4 requires that nothing
outside ``colorama/tests/`` changed, so any edit, addition or removal of a
library module fails this test.
"""
import hashlib
from pathlib import Path

import pytest

PACKAGE_DIR = Path(__file__).resolve().parent.parent

BASELINE_SHA256 = {
    "__init__.py": "3dcf10458fd6ffa4d94f277c86ffcbce43534a1dab8b45b9074b134bce8d1216",
    "ansi.py": "e5eb50c181d4a60eb7b436be08dcb7ed7b4640dffb0f9bc197bb05647d77effa",
    "ansitowin32.py": "a4db86d83aeaf3e920d5be2c0f0b4ce8cbb93fae523ce8f31e8e3781e98cc271",
    "initialise.py": "2aa19f1866f4cae7b47ea2268a78edd9c2df7f2cfe5e391745c9fa4973909fb5",
    "win32.py": "61038ac0c4f0b4605bb18e1d2f91d84efc1378ff70210adae4cbcf35d769c59b",
    "winterm.py": "7dd28e56b8b05a8007cb48172b895aa2727670863731e152fffa74da6ddb055a",
}


def test_library_module_set_is_unchanged():
    actual = {path.name for path in PACKAGE_DIR.glob("*.py")}
    assert actual == set(BASELINE_SHA256)


@pytest.mark.parametrize("name, digest", sorted(BASELINE_SHA256.items()))
def test_library_module_is_unchanged(name, digest):
    path = PACKAGE_DIR / name
    assert path.is_file(), f"{name} is missing from {PACKAGE_DIR}"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, (
        f"{name} was modified; only colorama/tests/ may change during this migration"
    )
