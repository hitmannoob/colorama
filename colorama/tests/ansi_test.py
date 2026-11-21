# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
import sys

import pytest

from ..ansi import Back, Fore, Style
from ..ansitowin32 import AnsiToWin32

stdout_orig = sys.stdout
stderr_orig = sys.stderr


@pytest.fixture(autouse=True)
def reset_streams():
    # sanity check: stdout should be a file or StringIO object.
    # It will only be AnsiToWin32 if init() has previously wrapped it
    assert not isinstance(sys.stdout, AnsiToWin32)
    assert not isinstance(sys.stderr, AnsiToWin32)
    yield
    sys.stdout = stdout_orig
    sys.stderr = stderr_orig


@pytest.mark.parametrize(
    "code, expected",
    [
        (Fore.BLACK, "\033[30m"),
        (Fore.RED, "\033[31m"),
        (Fore.GREEN, "\033[32m"),
        (Fore.YELLOW, "\033[33m"),
        (Fore.BLUE, "\033[34m"),
        (Fore.MAGENTA, "\033[35m"),
        (Fore.CYAN, "\033[36m"),
        (Fore.WHITE, "\033[37m"),
        (Fore.RESET, "\033[39m"),
        # Check the light, extended versions.
        (Fore.LIGHTBLACK_EX, "\033[90m"),
        (Fore.LIGHTRED_EX, "\033[91m"),
        (Fore.LIGHTGREEN_EX, "\033[92m"),
        (Fore.LIGHTYELLOW_EX, "\033[93m"),
        (Fore.LIGHTBLUE_EX, "\033[94m"),
        (Fore.LIGHTMAGENTA_EX, "\033[95m"),
        (Fore.LIGHTCYAN_EX, "\033[96m"),
        (Fore.LIGHTWHITE_EX, "\033[97m"),
    ],
)
def test_fore_attributes(code, expected):
    assert code == expected


@pytest.mark.parametrize(
    "code, expected",
    [
        (Back.BLACK, "\033[40m"),
        (Back.RED, "\033[41m"),
        (Back.GREEN, "\033[42m"),
        (Back.YELLOW, "\033[43m"),
        (Back.BLUE, "\033[44m"),
        (Back.MAGENTA, "\033[45m"),
        (Back.CYAN, "\033[46m"),
        (Back.WHITE, "\033[47m"),
        (Back.RESET, "\033[49m"),
        # Check the light, extended versions.
        (Back.LIGHTBLACK_EX, "\033[100m"),
        (Back.LIGHTRED_EX, "\033[101m"),
        (Back.LIGHTGREEN_EX, "\033[102m"),
        (Back.LIGHTYELLOW_EX, "\033[103m"),
        (Back.LIGHTBLUE_EX, "\033[104m"),
        (Back.LIGHTMAGENTA_EX, "\033[105m"),
        (Back.LIGHTCYAN_EX, "\033[106m"),
        (Back.LIGHTWHITE_EX, "\033[107m"),
    ],
)
def test_back_attributes(code, expected):
    assert code == expected


@pytest.mark.parametrize(
    "code, expected",
    [
        (Style.DIM, "\033[2m"),
        (Style.NORMAL, "\033[22m"),
        (Style.BRIGHT, "\033[1m"),
    ],
)
def test_style_attributes(code, expected):
    assert code == expected
