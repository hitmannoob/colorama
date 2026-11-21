# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
import sys
from unittest.mock import Mock, patch

import pytest

from ..winterm import WinColor, WinStyle, WinTerm


@patch('colorama.winterm.win32')
def testInit(mockWin32):
    mockAttr = Mock()
    mockAttr.wAttributes = 7 + 6 * 16 + 8
    mockWin32.GetConsoleScreenBufferInfo.return_value = mockAttr
    term = WinTerm()
    assert term._fore == 7
    assert term._back == 6
    assert term._style == 8


@pytest.mark.skipif(
    not sys.platform.startswith("win"), reason="requires Windows"
)
def testGetAttrs():
    term = WinTerm()

    term._fore = 0
    term._back = 0
    term._style = 0
    assert term.get_attrs() == 0

    term._fore = WinColor.YELLOW
    assert term.get_attrs() == WinColor.YELLOW

    term._back = WinColor.MAGENTA
    assert term.get_attrs() == WinColor.YELLOW + WinColor.MAGENTA * 16

    term._style = WinStyle.BRIGHT
    assert (
        term.get_attrs()
        == WinColor.YELLOW + WinColor.MAGENTA * 16 + WinStyle.BRIGHT
    )


@patch('colorama.winterm.win32')
def testResetAll(mockWin32):
    mockAttr = Mock()
    mockAttr.wAttributes = 1 + 2 * 16 + 8
    mockWin32.GetConsoleScreenBufferInfo.return_value = mockAttr
    term = WinTerm()

    term.set_console = Mock()
    term._fore = -1
    term._back = -1
    term._style = -1

    term.reset_all()

    assert term._fore == 1
    assert term._back == 2
    assert term._style == 8
    assert term.set_console.called is True


@pytest.mark.skipif(
    not sys.platform.startswith("win"), reason="requires Windows"
)
@pytest.mark.parametrize(
    "method, attribute, value",
    [
        ("fore", "_fore", 5),
        ("back", "_back", 5),
        ("style", "_style", 22),
    ],
)
def testConsoleAttributeSetter(method, attribute, value):
    term = WinTerm()
    term.set_console = Mock()
    setattr(term, attribute, 0)

    getattr(term, method)(value)

    assert getattr(term, attribute) == value
    assert term.set_console.called is True


@patch('colorama.winterm.win32')
def testSetConsole(mockWin32):
    mockAttr = Mock()
    mockAttr.wAttributes = 0
    mockWin32.GetConsoleScreenBufferInfo.return_value = mockAttr
    term = WinTerm()
    term.windll = Mock()

    term.set_console()

    assert mockWin32.SetConsoleTextAttribute.call_args == (
        (mockWin32.STDOUT, term.get_attrs()),
        {},
    )


@patch('colorama.winterm.win32')
def testSetConsoleOnStderr(mockWin32):
    mockAttr = Mock()
    mockAttr.wAttributes = 0
    mockWin32.GetConsoleScreenBufferInfo.return_value = mockAttr
    term = WinTerm()
    term.windll = Mock()

    term.set_console(on_stderr=True)

    assert mockWin32.SetConsoleTextAttribute.call_args == (
        (mockWin32.STDERR, term.get_attrs()),
        {},
    )
