# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
import sys

import pytest

from ..ansitowin32 import StreamWrapper, AnsiToWin32


def is_a_tty(stream):
    return StreamWrapper(stream, None).isatty()


@pytest.mark.parametrize(
    "stream_fixture, expected",
    [
        ("stream_tty", True),
        ("stream_non_tty", False),
    ],
)
def test_isatty(stream_fixture, expected, request, pycharm):
    stream = request.getfixturevalue(stream_fixture)
    assert is_a_tty(stream) is expected
    with pycharm():
        assert is_a_tty(stream) is expected


def test_withPycharm(pycharm):
    with pycharm():
        assert is_a_tty(sys.stderr)
        assert is_a_tty(sys.stdout)


def test_withPycharmTTYOverride(pycharm, replace_by, stream_tty):
    with pycharm(), replace_by(stream_tty):
        assert is_a_tty(stream_tty)


def test_withPycharmNonTTYOverride(pycharm, replace_by, stream_non_tty):
    with pycharm(), replace_by(stream_non_tty):
        assert not is_a_tty(stream_non_tty)


def test_withPycharmNoneOverride(
    pycharm, replace_by, replace_original_by, stream_tty, stream_non_tty
):
    with pycharm():
        with replace_by(None), replace_original_by(None):
            assert not is_a_tty(None)
            assert not is_a_tty(stream_non_tty)
            assert is_a_tty(stream_tty)


def test_withPycharmStreamWrapped(pycharm, stream_tty, stream_non_tty):
    with pycharm():
        assert AnsiToWin32(stream_tty).stream.isatty()
        assert not AnsiToWin32(stream_non_tty).stream.isatty()
        assert AnsiToWin32(sys.stdout).stream.isatty()
        assert AnsiToWin32(sys.stderr).stream.isatty()
