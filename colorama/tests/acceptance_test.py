# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
"""Guard tests for the unittest -> pytest migration acceptance criteria.

These tests inspect the repository itself rather than exercising colorama, so a
regression in a converted module is caught even when that module's own tests
still pass. Criterion 4 (production sources unchanged) is covered by
source_integrity_test.py.
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent


def _test_modules():
    return sorted(
        path
        for path in TESTS_DIR.glob("*.py")
        if path.name not in {"conftest.py", "__init__.py"}
    )


def _migration_baseline():
    migration = REPO_ROOT / "MIGRATION.md"
    assert migration.is_file(), "MIGRATION.md must record the unittest baseline"
    text = migration.read_text(encoding="utf-8")
    match = re.search(
        r"(?:ran|baseline|collected)[^0-9]{0,40}(\d+)\s+tests?", text, re.IGNORECASE
    )
    if match is None:
        match = re.search(r"(\d+)\s+tests?", text, re.IGNORECASE)
    assert match is not None, "MIGRATION.md must contain the unittest test count"
    return int(match.group(1))


def test_migration_records_unittest_baseline():
    assert _migration_baseline() >= 52


def test_pytest_collects_at_least_baseline():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "colorama/tests"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    match = re.search(r"(\d+)\s+tests?\s+collected", output)
    assert match is not None, f"could not parse pytest collection output:\n{output}"
    assert int(match.group(1)) >= _migration_baseline()


def _class_bases(node):
    for base in node.bases:
        if isinstance(base, ast.Name):
            yield base.id
        elif isinstance(base, ast.Attribute):
            yield base.attr


def test_no_unittest_testcase_subclasses():
    offenders = []
    for path in _test_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for name in _class_bases(node):
                    if name == "TestCase" or name.endswith("TestCase"):
                        offenders.append(f"{path.name}:{node.lineno} class {node.name}")
    assert not offenders, "unittest.TestCase subclasses remain: " + ", ".join(offenders)


def test_no_self_assert_calls():
    offenders = []
    for path in _test_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr.startswith("assert")
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"
            ):
                offenders.append(f"{path.name}:{node.lineno} self.{func.attr}()")
    assert not offenders, "self.assert* calls remain: " + ", ".join(offenders)
