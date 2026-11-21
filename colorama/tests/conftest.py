# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
"""Shared pytest fixtures for colorama's test suite.

These replace the helper classes and context managers that used to live in
``colorama/tests/utils.py``.
"""
from contextlib import contextmanager
from io import StringIO
import os
import sys

import pytest


class StreamTTY(StringIO):
    def isatty(self):
        return True


class StreamNonTTY(StringIO):
    def isatty(self):
        return False


@contextmanager
def _osname(name):
    orig = os.name
    os.name = name
    try:
        yield
    finally:
        os.name = orig


@contextmanager
def _replace_by(stream):
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    sys.stdout = stream
    sys.stderr = stream
    try:
        yield
    finally:
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr


@contextmanager
def _replace_original_by(stream):
    orig_stdout = sys.__stdout__
    orig_stderr = sys.__stderr__
    sys.__stdout__ = stream
    sys.__stderr__ = stream
    try:
        yield
    finally:
        sys.__stdout__ = orig_stdout
        sys.__stderr__ = orig_stderr


@contextmanager
def _pycharm():
    os.environ["PYCHARM_HOSTED"] = "1"
    non_tty = StreamNonTTY()
    try:
        with _replace_by(non_tty), _replace_original_by(non_tty):
            yield
    finally:
        del os.environ["PYCHARM_HOSTED"]


@pytest.fixture
def osname():
    """Return the ``os.name`` context manager."""
    return _osname


@pytest.fixture
def replace_by():
    """Return the ``sys.stdout``/``sys.stderr`` replacement context manager."""
    return _replace_by


@pytest.fixture
def replace_original_by():
    """Return the ``sys.__stdout__``/``sys.__stderr__`` replacement context manager."""
    return _replace_original_by


@pytest.fixture
def pycharm():
    """Return the PyCharm-hosted environment context manager."""
    return _pycharm


@pytest.fixture
def stream_tty():
    """Return a TTY-like stream instance."""
    return StreamTTY()


@pytest.fixture
def stream_non_tty():
    """Return a non-TTY-like stream instance."""
    return StreamNonTTY()


@pytest.fixture
def tty_stream():
    """Return the TTY-like stream class."""
    return StreamTTY


@pytest.fixture
def non_tty_stream():
    """Return the non-TTY-like stream class."""
    return StreamNonTTY
