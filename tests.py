#!/usr/bin/env python3
import io
import logging
import os
import pathlib
import re
import sys
import tempfile
import unittest
from typing import Iterable, NamedTuple, Union

# Resolve local module
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), os.path.pardir)
)  # noqa
from apexlint import base, pathtools, unittesttools  # isort:skip


# Other tests #################################################################


class TestMatchFiles(unittesttools.ValidatorTestCase):
    def test_stdin(self):
        """Validate standard input."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")

        class Case(NamedTuple):
            contents: str
            expected: Iterable[str]

        for c in (
            Case("", ()),
            Case(" ", ()),
            Case("FOO", ("<stdin>:1:0: error: Found FOO",)),
            Case(
                "FOO FOO",
                (
                    "<stdin>:1:0: error: Found FOO",
                    "<stdin>:1:4: error: Found FOO",
                ),
            ),
        ):
            with self.subTest(c):
                self.assertMatchFiles(
                    validator=Validator,
                    paths=[pathtools.StdIn(io.StringIO(c.contents))],
                    expected=c.expected,
                    verbose=-1,
                )

    def test_files(self):
        """Validate that actual files are checked."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")

        with tempfile.TemporaryDirectory() as tmpdir:
            with pathtools.chdir(tmpdir):

                class File(NamedTuple):
                    filename: str
                    contents: str

                for f in (
                    File("Foo.cls", "FOO"),
                    File("src/classes/Foo.cls", "FOO"),
                ):
                    path = pathlib.Path(f.filename)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open(mode="w") as fd:
                        fd.write(f.contents)

                class Case(NamedTuple):
                    path: str
                    expected: Iterable[str]

                for c in (
                    Case(
                        path="Foo.cls",
                        expected=("Foo.cls:1:0: error: Found FOO",),
                    ),
                    Case(
                        path="src/classes/Foo.cls",
                        expected=(
                            "src/classes/Foo.cls:1:0: error: Found FOO",
                        ),
                    ),
                ):
                    with self.subTest(c):
                        self.assertMatchFiles(
                            validator=Validator,
                            paths=[pathlib.Path(c.path)],
                            expected=c.expected,
                            verbose=-1,
                        )


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

    def test_verbose(self):
        """Validate verbose settings."""

        class Validator(base.Validator):
            """Found FOO
            Instead of FOO, use BAR.
            """

            invalid = re.compile(r"(?P<cursor>FOO)")

        class Case(NamedTuple):
            verbose: int
            expected: Iterable[str]

        for c in (
            Case(
                -1,
                (
                    """\
                    Foo.cls:1:0: error: Found FOO
                    """,
                ),
            ),
            Case(
                0,
                (
                    """\
                    Foo.cls:1:0: error: Found FOO
                     FOO
                     ^~~
                    """,
                ),
            ),
            Case(
                1,
                (
                    """\
                    Foo.cls:1:0: error: Found FOO
                      Instead of FOO, use BAR.
                     FOO
                     ^~~
                    """,
                ),
            ),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=Validator,
                    contents="FOO",
                    expected=c.expected,
                    verbose=c.verbose,
                )

    def test_filenames_default(self):
        """Default `Validator.filename`` is respected."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")

        class Case(NamedTuple):
            filename: str
            expected: bool

        for c in (
            Case("Foo.cls", ("Foo.cls:1:0: error: Found FOO",)),
            Case("Foo.trigger", ("Foo.trigger:1:0: error: Found FOO",)),
            Case("Foo", ()),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=Validator,
                    contents="FOO",
                    expected=c.expected,
                    path=pathlib.Path(c.filename),
                    verbose=-1,
                )

    def test_filenames_none(self):
        """Empty `Validator.filename`` is respected."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")
            filenames = ()

        class Case(NamedTuple):
            filename: str
            expected: bool

        for c in (
            Case("Foo.cls", ()),
            Case("Foo.trigger", ()),
            Case("Foo", ()),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=Validator,
                    contents="FOO",
                    expected=c.expected,
                    path=pathlib.Path(c.filename),
                    verbose=-1,
                )

    def test_filenames_custom(self):
        """Custom `Validator.filename`` is respected."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")
            filenames = ("*Test*.cls",)

        class Case(NamedTuple):
            filename: str
            expected: bool

        for c in (
            Case("Foo.cls", ()),
            Case("Foo_Test.cls", ("Foo_Test.cls:1:0: error: Found FOO",)),
            Case("TestFoo.cls", ("TestFoo.cls:1:0: error: Found FOO",)),
            Case("Foo", ()),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=Validator,
                    contents="FOO",
                    expected=c.expected,
                    path=pathlib.Path(c.filename),
                    verbose=-1,
                )


class TestPathtools(unittesttools.PathLikeTestCase):
    def test_paths(self):
        class Case(NamedTuple):
            filename: str
            expected: os.PathLike

        for c in (
            Case("-", pathtools.stdin),
            Case("./-", pathlib.Path("-")),
            Case("Foo.cls", pathlib.Path("Foo.cls")),
        ):
            with self.subTest(c):
                self.assertSamePaths(
                    pathtools.paths([c.filename]), [c.expected]
                )

    def test_unique(self):
        class Case(NamedTuple):
            filenames: Iterable[str]
            expected: Iterable[str]

        for c in (
            Case([], []),
            Case(["Foo.cls"], ["Foo.cls"]),
            Case(["Foo.cls", "Bar.cls", "Foo.cls"], ["Foo.cls", "Bar.cls"]),
        ):
            with self.subTest(c):
                self.assertSamePaths(
                    pathtools.unique(pathlib.Path(n) for n in c.filenames),
                    c.expected,
                )

    def test_walk(self):
        with tempfile.TemporaryDirectory() as dname:
            d = pathlib.Path(dname)

            # Populate test directory
            for filename in ("-", "Foo.cls", "src/classes/Bar.cls"):
                path = d.joinpath(filename)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch(exist_ok=True)

            class Case(NamedTuple):
                paths: Iterable[Union[pathlib.Path, str]]
                expected: Iterable[Union[pathlib.Path, str]]

                @staticmethod
                def testdir(p: Union[pathlib.Path, str]) -> pathlib.Path:
                    return p if isinstance(p, pathlib.Path) else d.joinpath(p)

            for c in (
                Case([], []),
                # Files
                Case(["Foo.cls"], ["Foo.cls"]),
                Case(["-"], ["-"]),
                Case(["Missing.cls"], ["Missing.cls"]),
                # Directory
                Case(["src"], ["src/classes/Bar.cls"]),
                Case(["missing/"], ["missing"]),
                # Standard input
                Case([pathtools.stdin], [pathtools.stdin]),
            ):
                with self.subTest(c):
                    self.assertSamePaths(
                        pathtools.walk(c.testdir(p) for p in c.paths),
                        [c.testdir(p) for p in c.expected],
                    )


class TestPathtoolsStdIn(unittest.TestCase):
    def test_equal(self):
        self.assertEqual(pathtools.stdin, pathtools.stdin)
        self.assertEqual(pathtools.StdIn(), pathtools.StdIn())

    def test_str(self):
        self.assertEqual(repr(pathtools.stdin), "StdIn()")
        self.assertEqual(str(pathtools.stdin), "<stdin>")

    def test_pathtools(self):
        self.assertEqual(pathtools.stdin.is_dir(), False)
        self.assertEqual(pathtools.stdin.open(), sys.stdin)
        self.assertEqual(pathtools.stdin.resolve(), pathtools.stdin)

    def test_typeof(self):
        self.assertTrue(pathtools.StdIn.typeof(pathtools.stdin))
        self.assertFalse(pathtools.StdIn.typeof(pathlib.Path("")))


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)  # Tests shouldn't spew logs
    unittest.main()
