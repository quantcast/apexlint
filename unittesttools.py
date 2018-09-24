import os
import pathlib
import textwrap
import unittest
from typing import Iterable, Optional, Type, Union

from . import base, match


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
        verbose: int = 0,
    ):
        self.assertEqual(
            list(
                match.render(
                    paths=paths, validators=(validator,), verbose=verbose
                )
            ),
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
        verbose: int = 0,
    ):
        self.assertEqual(
            [
                e.render(verbose=verbose)
                for e in match.lines(
                    contents.splitlines(), path=path, validators=(validator,)
                )
            ],
            [textwrap.dedent(e).rstrip("\n") for e in expected],
            msg=msg,
        )
