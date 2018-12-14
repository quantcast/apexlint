# Copyright 2018-19 Quantcast Corporation. All rights reserved.
#
# This file is part of Quantcast Apex Linter for Salesforce
#
# Licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
#
import os
import pathlib
import textwrap
import unittest
from typing import Iterable, Optional, Type, Union

from . import base, match, terminfo


class PathLikeTestCase(unittest.TestCase):
    """Provide additional asserts for `PathLike` representations. `"""

    @staticmethod
    def _normalize_path(
        path: Union[os.PathLike, str],
        *,
        start: Optional[Union[os.PathLike, str]],
    ):
        if start:
            path = os.path.relpath(path, start=start)
        if not isinstance(path, os.PathLike):
            path = pathlib.Path(path)
        return path

    def assertSamePath(
        self,
        first: os.PathLike,
        second: os.PathLike,
        msg: Optional[str] = None,
        *,
        start: Optional[os.PathLike] = None,
    ):
        first, second = (
            self._normalize_path(p, start=start) for p in (first, second)
        )
        self.assertEqual(first, second, msg=msg)

    def assertSamePaths(
        self,
        first: Iterable[os.PathLike],
        second: Iterable[os.PathLike],
        msg: Optional[str] = None,
        *,
        start: Optional[os.PathLike] = None,
    ):
        first, second = (
            [self._normalize_path(p, start=start) for p in paths]
            for paths in (first, second)
        )
        self.assertEqual(first, second, msg=msg)


class ValidatorTestCase(unittest.TestCase):
    """Provide additional asserts for `Validator`` class."""

    def assertMatchFiles(
        self,
        *,
        validator: Type[base.Validator],
        paths: Iterable[pathlib.Path],
        expected: Iterable[str],
        msg: str = None,
        term: Optional[Type[terminfo.TermInfo]] = None,
        verbose: int = 0,
    ):
        self.assertEqual(
            [
                str(m)
                for m in match.render(
                    paths=paths,
                    term=term,
                    validators=(validator,),
                    verbose=verbose,
                )
            ],
            [textwrap.dedent(e).rstrip("\n") for e in expected],
            msg=msg,
        )

    def assertMatchLines(
        self,
        *,
        validator: Type[base.Validator],
        contents: str,
        expected: Iterable[str],
        msg: str = None,
        path: pathlib.Path = pathlib.Path("Foo.cls"),
        suppress: bool = True,
        term: Optional[Type[terminfo.TermInfo]] = None,
        verbose: int = 0,
    ):
        self.assertEqual(
            [
                e.render(term=term, verbose=verbose)
                for e in match.lines(
                    contents.splitlines(),
                    path=path,
                    suppress=suppress,
                    validators=(validator,),
                )
            ],
            [textwrap.dedent(e).rstrip("\n") for e in expected],
            msg=msg,
        )
