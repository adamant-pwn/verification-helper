import os
import platform
import textwrap
import unittest
from typing import *
from unittest import mock

import onlinejudge_verify.languages.cplusplus as cplusplus
import tests.utils


class TestCPlusPlusEnvironments(unittest.TestCase):
    def test_windows_stack_flags(self) -> None:
        config = {'environments': [{'CXX': 'g++'}, {'CXX': 'clang++'}, {'CXX': 'clang++', 'CXXFLAGS': ['-O0']}]}
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(platform, 'system', return_value='Windows'), mock.patch.object(cplusplus.subprocess, 'check_output', side_effect=[b'x86_64-w64-mingw32', b'x86_64-pc-windows-msvc']) as probe:
            envs = cplusplus.CPlusPlusLanguage(config=config)._list_environments()
            self.assertEqual([env.CXXFLAGS[-1] for env in envs], ['-Wl,-stack,0x10000000', '-Wl,/STACK:0x10000000', '-O0'])
            self.assertEqual(envs[2].CXXFLAGS, ['-O0'])
            self.assertEqual(probe.call_args_list, [mock.call(['g++', '-dumpmachine']), mock.call(['clang++', '-dumpmachine'])])


class TestCPlusPlusListDependencies(unittest.TestCase):
    """TestCPlusPlusListDependencies has unit tests for the feature to list dependencies of C++ files.
    """
    def test_success(self) -> None:
        files = {
            'main.cpp': textwrap.dedent("""\
                #include "included.hpp"
                """).encode(),
            'included.hpp': textwrap.dedent("""\
                int main() {}
                """).encode(),
        }

        with tests.utils.load_files(files=files) as tempdir:
            with tests.utils.chdir(tempdir):
                expected = sorted([tempdir / 'main.cpp', tempdir / 'included.hpp'])
                actual = sorted(cplusplus.CPlusPlusLanguage().list_dependencies(tempdir / 'main.cpp', basedir=tempdir))
                self.assertEqual(actual, expected)

    @unittest.skipIf(platform.system() == 'Windows', "The path separator should be '/' for this test.")
    def test_failure_with_backslash(self) -> None:
        files = {
            'main.cpp': textwrap.dedent("""\
                #include ".\\included.hpp"
                """).encode(),
            'included.hpp': textwrap.dedent("""\
                int main() {}
                """).encode(),
        }

        with tests.utils.load_files(files=files) as tempdir:
            with tests.utils.chdir(tempdir):
                self.assertRaises(Exception, lambda: cplusplus.CPlusPlusLanguage().list_dependencies(tempdir / 'main.cpp', basedir=tempdir))

    @unittest.skipIf(platform.system() in ('Windows', 'Darwin'), "The filesystem should be case-sensitive for this test.")
    def test_failure_with_case_insensitive(self) -> None:
        files = {
            'main.cpp': textwrap.dedent("""\
                #include "INCLUDED.HPP"
                """).encode(),
            'included.hpp': textwrap.dedent("""\
                int main() {}
                """).encode(),
        }

        with tests.utils.load_files(files=files) as tempdir:
            with tests.utils.chdir(tempdir):
                self.assertRaises(Exception, lambda: cplusplus.CPlusPlusLanguage().list_dependencies(tempdir / 'main.cpp', basedir=tempdir))
