import pathlib
import textwrap
import unittest
from typing import Iterable, Type

from . import base, match


class ValidatorTestCase(unittest.TestCase):
    """Provide additional asserts for `Validator`` class."""

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
