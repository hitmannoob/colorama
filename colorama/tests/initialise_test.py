# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
import os
import sys
from unittest.mock import patch, Mock

import pytest

from ..ansitowin32 import StreamWrapper
from ..initialise import init, just_fix_windows_console, _wipe_internal_state_for_tests

orig_stdout = sys.stdout
orig_stderr = sys.stderr


def assert_wrapped():
    assert sys.stdout is not orig_stdout, 'stdout should be wrapped'
    assert sys.stderr is not orig_stderr, 'stderr should be wrapped'
    assert isinstance(sys.stdout, StreamWrapper), 'bad stdout wrapper'
    assert isinstance(sys.stderr, StreamWrapper), 'bad stderr wrapper'


def assert_not_wrapped():
    assert sys.stdout is orig_stdout, 'stdout should not be wrapped'
    assert sys.stderr is orig_stderr, 'stderr should not be wrapped'


@pytest.fixture(autouse=True)
def reset_state():
    orig_os_name = os.name

    def _reset():
        _wipe_internal_state_for_tests()
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        os.name = orig_os_name

    _reset()
    yield _reset
    _reset()


@pytest.mark.skipif(not sys.stdout.isatty(), reason="sys.stdout is not a tty")
class TestInit:

    @patch('colorama.initialise.reset_all')
    @patch('colorama.ansitowin32.winapi_test', lambda *_: True)
    @patch('colorama.ansitowin32.enable_vt_processing', lambda *_: False)
    def testInitWrapsOnWindows(self, _, osname):
        with osname("nt"):
            init()
            assert_wrapped()

    @patch('colorama.initialise.reset_all')
    @patch('colorama.ansitowin32.winapi_test', lambda *_: False)
    def testInitDoesntWrapOnEmulatedWindows(self, _, osname):
        with osname("nt"):
            init()
            assert_not_wrapped()

    def testInitDoesntWrapOnNonWindows(self, osname):
        with osname("posix"):
            init()
            assert_not_wrapped()

    def testInitDoesntWrapIfNone(self, replace_by):
        with replace_by(None):
            init()
            # We can't use assert_not_wrapped here because replace_by(None)
            # changes stdout/stderr already.
            assert sys.stdout is None
            assert sys.stderr is None

    def testInitAutoresetOnWrapsOnAllPlatforms(self, osname):
        with osname("posix"):
            init(autoreset=True)
            assert_wrapped()

    def testInitWrapOffDoesntWrapOnWindows(self, osname):
        with osname("nt"):
            init(wrap=False)
            assert_not_wrapped()

    def testInitWrapOffIncompatibleWithAutoresetOn(self):
        with pytest.raises(ValueError):
            init(autoreset=True, wrap=False)

    @patch('colorama.win32.SetConsoleTextAttribute')
    @patch('colorama.initialise.AnsiToWin32')
    def testAutoResetPassedOn(self, mockATW32, _, osname):
        with osname("nt"):
            init(autoreset=True)
            assert len(mockATW32.call_args_list) == 2
            assert mockATW32.call_args_list[1][1]['autoreset'] is True
            assert mockATW32.call_args_list[0][1]['autoreset'] is True

    @patch('colorama.initialise.AnsiToWin32')
    def testAutoResetChangeable(self, mockATW32, osname):
        with osname("nt"):
            init()

            init(autoreset=True)
            assert len(mockATW32.call_args_list) == 4
            assert mockATW32.call_args_list[2][1]['autoreset'] is True
            assert mockATW32.call_args_list[3][1]['autoreset'] is True

            init()
            assert len(mockATW32.call_args_list) == 6
            assert mockATW32.call_args_list[4][1]['autoreset'] is False
            assert mockATW32.call_args_list[5][1]['autoreset'] is False

    @patch('colorama.initialise.atexit.register')
    def testAtexitRegisteredOnlyOnce(self, mockRegister):
        init()
        assert mockRegister.called
        mockRegister.reset_mock()
        init()
        assert not mockRegister.called


class TestJustFixWindowsConsole:

    @patch("colorama.ansitowin32.winapi_test", lambda: True)
    def testJustFixWindowsConsole(self, reset_state):
        if sys.platform != "win32":
            # just_fix_windows_console should be a no-op
            just_fix_windows_console()
            assert sys.stdout is orig_stdout
            assert sys.stderr is orig_stderr
        else:
            def fake_std():
                # Emulate stdout=not a tty, stderr=tty
                # to check that we handle both cases correctly
                stdout = Mock()
                stdout.closed = False
                stdout.isatty.return_value = False
                stdout.fileno.return_value = 1
                sys.stdout = stdout

                stderr = Mock()
                stderr.closed = False
                stderr.isatty.return_value = True
                stderr.fileno.return_value = 2
                sys.stderr = stderr

            for native_ansi in [False, True]:
                with patch(
                    'colorama.ansitowin32.enable_vt_processing',
                    lambda *_: native_ansi
                ):
                    reset_state()
                    fake_std()

                    # Regular single-call test
                    prev_stdout = sys.stdout
                    prev_stderr = sys.stderr
                    just_fix_windows_console()
                    assert sys.stdout is prev_stdout
                    if native_ansi:
                        assert sys.stderr is prev_stderr
                    else:
                        assert sys.stderr is not prev_stderr

                    # second call without resetting is always a no-op
                    prev_stdout = sys.stdout
                    prev_stderr = sys.stderr
                    just_fix_windows_console()
                    assert sys.stdout is prev_stdout
                    assert sys.stderr is prev_stderr

                    reset_state()
                    fake_std()

                    # If init() runs first, just_fix_windows_console should be a no-op
                    init()
                    prev_stdout = sys.stdout
                    prev_stderr = sys.stderr
                    just_fix_windows_console()
                    assert prev_stdout is sys.stdout
                    assert prev_stderr is sys.stderr
