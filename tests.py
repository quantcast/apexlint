#!/usr/bin/env python3
import logging
import os
import re
import sys
import unittest
from typing import Iterable, NamedTuple

# Resolve local module
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), os.path.pardir)
)  # noqa
from apexlint import base, unittesttools  # isort:skip


# Other tests #################################################################
class TestMatchLines(unittesttools.ValidatorTestCase):
    def test_no_context(self):
        """Validate without context."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")

        class Case(NamedTuple):
            contents: str
            expected: Iterable[str]

        for c in (
            Case("", ()),
            Case(" ", ()),
            Case("FOO", ("Foo.cls:1:0: error: Found FOO",)),
            Case(
                "FOO FOO",
                (
                    "Foo.cls:1:0: error: Found FOO",
                    "Foo.cls:1:4: error: Found FOO",
                ),
            ),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=Validator,
                    contents=c.contents,
                    expected=c.expected,
                    verbose=-1,
                )

    def test_without_cursor(self):
        """Validate without a <cursor> group."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")

        class Case(NamedTuple):
            contents: str
            expected: Iterable[str]

        for c in (
            Case("", ()),
            Case(" ", ()),
            Case(
                "FOO",
                (
                    """\
                    Foo.cls:1:0: error: Found FOO
                     FOO
                     ^
                    """,
                ),
            ),
            Case(
                "FOO FOO",
                (
                    """\
                    Foo.cls:1:0: error: Found FOO
                     FOO FOO
                     ^
                    """,
                    """\
                    Foo.cls:1:4: error: Found FOO
                     FOO FOO
                         ^
                    """,
                ),
            ),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=Validator,
                    contents=c.contents,
                    expected=c.expected,
                )

    def test_with_cursor(self):
        """Validate with a <cursor> group."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"(?P<cursor>FOO)")

        class Case(NamedTuple):
            contents: str
            expected: Iterable[str]

        for c in (
            Case("", ()),
            Case(" ", ()),
            Case(
                "FOO",
                (
                    """\
                    Foo.cls:1:0: error: Found FOO
                     FOO
                     ^~~
                    """,
                ),
            ),
            Case(
                "FOO FOO",
                (
                    """\
                    Foo.cls:1:0: error: Found FOO
                     FOO FOO
                     ^~~
                    """,
                    """\
                    Foo.cls:1:4: error: Found FOO
                     FOO FOO
                         ^~~
                    """,
                ),
            ),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=Validator,
                    contents=c.contents,
                    expected=c.expected,
                )


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)  # Tests shouldn't spew logs
    unittest.main()
