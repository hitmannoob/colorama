# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
from io import StringIO, TextIOWrapper
from unittest.mock import MagicMock, Mock, patch
from contextlib import ExitStack

import pytest

from ..ansitowin32 import AnsiToWin32, StreamWrapper
from ..win32 import ENABLE_VIRTUAL_TERMINAL_PROCESSING


class TestStreamWrapper:

    def testIsAProxy(self):
        mockStream = Mock()
        wrapper = StreamWrapper(mockStream, None)
        assert wrapper.random_attr is mockStream.random_attr

    def testDelegatesWrite(self):
        mockStream = Mock()
        mockConverter = Mock()
        wrapper = StreamWrapper(mockStream, mockConverter)
        wrapper.write('hello')
        assert mockConverter.write.call_args == (('hello',), {})

    def testDelegatesContext(self):
        mockConverter = Mock()
        s = StringIO()
        with StreamWrapper(s, mockConverter) as fp:
            fp.write('hello')
        assert s.closed

    def testProxyNoContextManager(self):
        mockStream = MagicMock()
        mockStream.__enter__.side_effect = AttributeError()
        mockConverter = Mock()
        with pytest.raises(AttributeError):
            with StreamWrapper(mockStream, mockConverter) as wrapper:
                wrapper.write('hello')

    def test_closed_shouldnt_raise_on_closed_stream(self):
        stream = StringIO()
        stream.close()
        wrapper = StreamWrapper(stream, None)
        assert wrapper.closed is True

    def test_closed_shouldnt_raise_on_detached_stream(self):
        stream = TextIOWrapper(StringIO())
        stream.detach()
        wrapper = StreamWrapper(stream, None)
        assert wrapper.closed is True


class TestAnsiToWin32:

    def testInit(self):
        mockStdout = Mock()
        auto = Mock()
        stream = AnsiToWin32(mockStdout, autoreset=auto)
        assert stream.wrapped == mockStdout
        assert stream.autoreset == auto

    @patch('colorama.ansitowin32.winterm', None)
    @patch('colorama.ansitowin32.winapi_test', lambda *_: True)
    def testStripIsTrueOnWindows(self):
        with patch('colorama.ansitowin32.os.name', 'nt'):
            mockStdout = Mock()
            stream = AnsiToWin32(mockStdout)
            assert stream.strip

    def testStripIsFalseOffWindows(self):
        with patch('colorama.ansitowin32.os.name', 'posix'):
            mockStdout = Mock(closed=False)
            stream = AnsiToWin32(mockStdout)
            assert not stream.strip

    def testWriteStripsAnsi(self):
        mockStdout = Mock()
        stream = AnsiToWin32(mockStdout)
        stream.wrapped = Mock()
        stream.write_and_convert = Mock()
        stream.strip = True

        stream.write('abc')

        assert not stream.wrapped.write.called
        assert stream.write_and_convert.call_args == (('abc',), {})

    def testWriteDoesNotStripAnsi(self):
        mockStdout = Mock()
        stream = AnsiToWin32(mockStdout)
        stream.wrapped = Mock()
        stream.write_and_convert = Mock()
        stream.strip = False
        stream.convert = False

        stream.write('abc')

        assert not stream.write_and_convert.called
        assert stream.wrapped.write.call_args == (('abc',), {})

    @pytest.mark.parametrize("convert, autoreset", [
        (True, True),
        (False, True),
        (True, False),
        (False, False),
    ])
    def testWriteAutoresets(self, convert, autoreset):
        stream = AnsiToWin32(Mock())
        stream.convert = convert
        stream.reset_all = Mock()
        stream.autoreset = autoreset
        stream.winterm = Mock()

        stream.write('abc')

        assert stream.reset_all.called == autoreset

    def testWriteAndConvertWritesPlainText(self):
        stream = AnsiToWin32(Mock())
        stream.write_and_convert('abc')
        assert stream.wrapped.write.call_args == (('abc',), {})

    @pytest.mark.parametrize("datum", [
        'abc\033[mdef',
        'abc\033[0mdef',
        'abc\033[2mdef',
        'abc\033[02mdef',
        'abc\033[002mdef',
        'abc\033[40mdef',
        'abc\033[040mdef',
        'abc\033[0;1mdef',
        'abc\033[40;50mdef',
        'abc\033[50;30;40mdef',
        'abc\033[Adef',
        'abc\033[0Gdef',
        'abc\033[1;20;128Hdef',
    ])
    def testWriteAndConvertStripsAllValidAnsi(self, datum):
        stream = AnsiToWin32(Mock())
        stream.call_win32 = Mock()
        stream.write_and_convert(datum)
        assert [
            args[0] for args in stream.wrapped.write.call_args_list
        ] == [('abc',), ('def',)]

    def testWriteAndConvertSkipsEmptySnippets(self):
        stream = AnsiToWin32(Mock())
        stream.call_win32 = Mock()
        stream.write_and_convert('\033[40m\033[41m')
        assert not stream.wrapped.write.called

    @pytest.mark.parametrize("datum, expected", [
        ('abc\033[adef', ('a', 'params')),
        ('abc\033[;;bdef', ('b', 'params')),
        ('abc\033[0cdef', ('c', 'params')),
        ('abc\033[;;0;;Gdef', ('G', 'params')),
        ('abc\033[1;20;128Hdef', ('H', 'params')),
    ])
    def testWriteAndConvertCallsWin32WithParamsAndCommand(self, datum, expected):
        stream = AnsiToWin32(Mock())
        stream.convert = True
        stream.call_win32 = Mock()
        stream.extract_params = Mock(return_value='params')
        stream.write_and_convert(datum)
        assert stream.call_win32.call_args[0] == expected

    def test_reset_all_shouldnt_raise_on_closed_orig_stdout(self):
        stream = StringIO()
        converter = AnsiToWin32(stream)
        stream.close()

        converter.reset_all()

    def test_wrap_shouldnt_raise_on_closed_orig_stdout(self):
        stream = StringIO()
        stream.close()
        with \
            patch("colorama.ansitowin32.os.name", "nt"), \
            patch("colorama.ansitowin32.winapi_test", lambda: True):
                converter = AnsiToWin32(stream)
        assert converter.strip
        assert not converter.convert

    def test_wrap_shouldnt_raise_on_missing_closed_attr(self):
        with \
            patch("colorama.ansitowin32.os.name", "nt"), \
            patch("colorama.ansitowin32.winapi_test", lambda: True):
                converter = AnsiToWin32(object())
        assert converter.strip
        assert not converter.convert

    @pytest.mark.parametrize("datum, expected", [
        ('', (0,)),
        (';;', (0,)),
        ('2', (2,)),
        (';;002;;', (2,)),
        ('0;1', (0, 1)),
        (';;003;;456;;', (3, 456)),
        ('11;22;33;44;55', (11, 22, 33, 44, 55)),
    ])
    def testExtractParams(self, datum, expected):
        stream = AnsiToWin32(Mock())
        assert stream.extract_params('m', datum) == expected

    def testCallWin32UsesLookup(self):
        listener = Mock()
        stream = AnsiToWin32(listener)
        stream.win32_calls = {
            1: (lambda *_, **__: listener(11),),
            2: (lambda *_, **__: listener(22),),
            3: (lambda *_, **__: listener(33),),
        }
        stream.call_win32('m', (3, 1, 99, 2))
        assert [a[0][0] for a in listener.call_args_list] == [33, 11, 22]

    @pytest.mark.parametrize("code, expected_calls", [
        ('\033]0\x07', 0),                      # missing arguments
        ('\033]0;foo\x08', 0),                  # wrong OSC command
        ('\033]0;colorama_test_title\x07', 1),  # should work
        ('\033]1;colorama_test_title\x07', 0),  # wrong set command
        ('\033]2;colorama_test_title\x07', 1),  # should work
        ('\033]' + ';' * 64 + '\x08', 0),       # see issue #247
    ])
    def test_osc_codes(self, code, expected_calls):
        mockStdout = Mock()
        stream = AnsiToWin32(mockStdout, convert=True)
        with patch('colorama.ansitowin32.winterm') as winterm:
            stream.write(code)
            assert winterm.set_title.call_count == expected_calls

    def test_native_windows_ansi(self):
        with ExitStack() as stack:
            def p(a, b):
                stack.enter_context(patch(a, b, create=True))
            # Pretend to be on Windows
            p("colorama.ansitowin32.os.name", "nt")
            p("colorama.ansitowin32.winapi_test", lambda: True)
            p("colorama.win32.winapi_test", lambda: True)
            p("colorama.winterm.win32.windll", "non-None")
            p("colorama.winterm.get_osfhandle", lambda _: 1234)

            # Pretend that our mock stream has native ANSI support
            p(
                "colorama.winterm.win32.GetConsoleMode",
                lambda _: ENABLE_VIRTUAL_TERMINAL_PROCESSING,
            )
            SetConsoleMode = Mock()
            p("colorama.winterm.win32.SetConsoleMode", SetConsoleMode)

            stdout = Mock()
            stdout.closed = False
            stdout.isatty.return_value = True
            stdout.fileno.return_value = 1

            # Our fake console says it has native vt support, so AnsiToWin32 should
            # enable that support and do nothing else.
            stream = AnsiToWin32(stdout)
            SetConsoleMode.assert_called_with(1234, ENABLE_VIRTUAL_TERMINAL_PROCESSING)
            assert not stream.strip
            assert not stream.convert
            assert not stream.should_wrap()

            # Now let's pretend we're on an old Windows console, that doesn't have
            # native ANSI support.
            p("colorama.winterm.win32.GetConsoleMode", lambda _: 0)
            SetConsoleMode = Mock()
            p("colorama.winterm.win32.SetConsoleMode", SetConsoleMode)

            stream = AnsiToWin32(stdout)
            SetConsoleMode.assert_called_with(1234, ENABLE_VIRTUAL_TERMINAL_PROCESSING)
            assert stream.strip
            assert stream.convert
            assert stream.should_wrap()
