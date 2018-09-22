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
    ):
        self.assertEqual(
            [
                str(e)
                for e in match.lines(
                    contents.splitlines(),
                    path=pathlib.Path("Foo.cls"),
                    validators=(validator,),
                )
            ],
            [textwrap.dedent(e).rstrip("\n") for e in expected],
            msg=msg,
        )
