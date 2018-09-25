#!/usr/bin/env python3
import io
import logging
import os
import pathlib
import re
import sys
import tempfile
import unittest
from typing import Iterable, NamedTuple, Pattern, Union

# Resolve local module
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), os.path.pardir)
)  # noqa
from apexlint import (  # isort:skip
    __main__,
    base,
    pathtools,
    retools,
    terminfo,
    unittesttools,
    validators,
)


# Validator tests #############################################################


class TestValidators(unittesttools.ValidatorTestCase):
    """`Validator` classes in `apexlint.validators`."""

    def test_NoComplexMapKeys(self):
        class Case(NamedTuple):
            contents: str
            expected: Iterable[str]

        for c in (
            # Base types are OK
            Case("new Map<Date, SObject>{}", ()),
            Case("new Map<DateTime, SObject>{}", ()),
            Case("new Map<Decimal, SObject>{}", ()),
            Case("new Map<Id, SObject>{}", ()),
            Case("new Map<Integer, SObject>{}", ()),
            Case("new Map<Long, SObject>{}", ()),
            Case("new Map<SObjectField, SObject>{}", ()),
            Case("new Map<SObjectType, SObject>{}", ()),
            Case("new Map<Schema.SObjectField, SObject>{}", ()),
            Case("new Map<Schema.SObjectType, SObject>{}", ()),
            Case("new Map<String, SObject>{}", ()),
            Case("new Map<System.Date, SObject>{}", ()),
            Case("new Map<System.DateTime, SObject>{}", ()),
            Case("new Map<System.Decimal, SObject>{}", ()),
            Case("new Map<System.Id, SObject>{}", ()),
            Case("new Map<System.Integer, SObject>{}", ()),
            Case("new Map<System.Long, SObject>{}", ()),
            Case("new Map<System.String, SObject>{}", ()),
            Case("new Map<System.Type, SObject>{}", ()),
            Case("new Map<Type, SObject>{}", ()),
            # Case should not matter
            Case("new map<id, sobject>{}", ()),
            Case("NEW MAP<ID, SOBJECT>{}", ()),
            # All other map keys fail
            Case(
                "new Map<SObject, SObject>{}",
                (
                    """\
                    Foo.cls:1:8: error: Map key is SObject or Object
                     new Map<SObject, SObject>{}
                             ^~~~~~~
                    """,
                ),
            ),
            # Suppression
            Case("new Map<A, B>{} // http://go.corp.qc/salesforce-maps", ()),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=validators.NoComplexMapKeys,
                    contents=c.contents,
                    expected=c.expected,
                )

    def test_NoFutureInTest(self):
        class Case(NamedTuple):
            filename: str
            contents: str
            expected: Iterable[str]

        for c in (
            Case(
                "FooTest.cls",
                "@future",
                (
                    """\
                    FooTest.cls:1:0: error: @future used in test class
                     @future
                     ^~~~~~~
                    """,
                ),
            ),
            Case(
                "FooTest.cls",
                "@Future",
                (
                    """\
                    FooTest.cls:1:0: error: @future used in test class
                     @Future
                     ^~~~~~~
                    """,
                ),
            ),
            Case(
                "TestUtils.cls",
                "@Future",
                (
                    """\
                    TestUtils.cls:1:0: error: @future used in test class
                     @Future
                     ^~~~~~~
                    """,
                ),
            ),
            Case(
                "UnitTestFactory.cls",
                "@Future",
                (
                    """\
                    UnitTestFactory.cls:1:0: error: @future used in test class
                     @Future
                     ^~~~~~~
                    """,
                ),
            ),
            # Ignore non-test files
            Case("Foo.cls", "@future", ()),
            Case("FooTest.trigger", "@future", ()),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=validators.NoFutureInTest,
                    contents=c.contents,
                    expected=c.expected,
                    path=pathlib.Path(c.filename),
                )


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

    def test_missing(self):
        """Validate that missing files are handled correctly."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")

        class Case(NamedTuple):
            path: str
            expected: Iterable[str]

        for c in (
            Case(
                path="Missing.cls",
                expected=(
                    "[Errno 2] No such file or directory: 'Missing.cls'",
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

    def test_count(self):
        """Validate counting of results"""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")

        class Case(NamedTuple):
            enabled: bool
            contents: str
            expected: int

        for c in (
            Case(True, "", "0"),
            Case(True, "FOO", "1"),
            Case(True, "FOO FOO", "2"),
            Case(False, "FOO", ""),
        ):
            with self.subTest(c):
                output_count = io.StringIO("\n")
                __main__.lint(
                    output=None,
                    output_count=output_count if c.enabled else None,
                    paths=[pathtools.StdIn(io.StringIO(c.contents))],
                    validators=[Validator],
                    verbose=-1,
                )
                # Last line should be the count
                self.assertEqual(
                    output_count.getvalue().splitlines()[-1],
                    c.expected,
                    msg=output_count.getvalue(),
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

    def test_terminfo(self):
        """Validate that terminfo controls color."""

        class Validator(base.Validator):
            """Found FOO
            Instead of FOO, use BAR.
            """

            invalid = re.compile(r"(?P<cursor>FOO)")

        class Case(NamedTuple):
            term: terminfo.TermInfo
            expected: Iterable[str]

        for c in (
            Case(
                terminfo.DumbTerm,
                (
                    """\
                    Foo.cls:1:0: error: Found FOO
                      Instead of FOO, use BAR.
                     FOO
                     ^~~
                    """,
                ),
            ),
            Case(
                terminfo.AnsiTerm,
                (
                    """\
                    \033[1mFoo.cls:1:0: \033[1;31merror:\033[0m Found FOO
                    \033[0;33m  Instead of FOO, use BAR.\033[0m
                     FOO
                     \033[0;31m^~~\033[0m
                    """,
                ),
            ),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=Validator,
                    contents="FOO",
                    expected=c.expected,
                    term=c.term,
                    verbose=1,
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

    def test_suppress(self):
        """`Validator.suppress` is respected."""

        class Validator(base.Validator):
            """Found FOO"""

            invalid = re.compile(r"FOO")
            suppress = retools.comment("ok")

        class Case(NamedTuple):
            contents: str
            expected: Iterable[str]

        for c in (
            Case("FOO", ("Foo.cls:1:0: error: Found FOO",)),
            Case("FOO '// ok'", ("Foo.cls:1:0: error: Found FOO",)),
            Case("FOO '/* ok */'", ("Foo.cls:1:0: error: Found FOO",)),
            Case("FOO // ok", ()),
            Case("FOO /* ok */", ()),
            Case("FOO '' // ok", ()),
            Case("FOO '' /* ok */", ()),
        ):
            with self.subTest(c):
                self.assertMatchLines(
                    validator=Validator,
                    contents=c.contents,
                    expected=c.expected,
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


class TestRetools(unittest.TestCase):
    def test_escape(self):
        class Case(NamedTuple):
            pattern: Union[Pattern, str]
            flags: int
            string: str
            expected: bool

        for c in (
            # Special characters
            Case(r".", flags=None, string=r".", expected=True),
            Case(r".", flags=None, string=r"x", expected=False),
            # Case sensitivity
            Case(r"a", flags=None, string=r"a", expected=True),
            Case(r"a", flags=None, string=r"A", expected=False),
            Case(r"a", flags=re.IGNORECASE, string=r"A", expected=True),
            # Patterns don't need to be escaped
            Case(re.compile(r"."), flags=None, string=r"x", expected=True),
            # Override flags
            Case(
                re.compile(r"a", flags=re.IGNORECASE),
                flags=None,
                string=r"A",
                expected=True,
            ),
            Case(
                re.compile(r"a", flags=re.IGNORECASE),
                flags=0,
                string=r"A",
                expected=False,
            ),
            Case(
                re.compile(r"a"),
                flags=re.IGNORECASE,
                string=r"A",
                expected=True,
            ),
        ):
            with self.subTest(c):
                assertExpected = (
                    self.assertTrue if c.expected else self.assertFalse
                )
                assertExpected(
                    retools.escape(c.pattern, flags=c.flags).search(c.string)
                )

    def test_comment(self):
        class Case(NamedTuple):
            pattern: Union[Pattern, str]
            string: str
            expected: bool

        for c in (
            # C-style comment
            Case(r"ok", string=r"/* ok */", expected=True),
            Case(r"ok", string=r"/* */ ok", expected=False),
            Case(r"ok", string=r"/* /* */ ok", expected=False),
            # C++-style comment
            Case(r"ok", string=r"// ok", expected=True),
            # Not in comment
            Case(r"ok", string=r"ok", expected=False),
            # Special characters
            Case(r".", string=r"// .", expected=True),
            Case(r".", string=r"// x", expected=False),
            # Case sensitivity
            Case(r"ok", string=r"// ok", expected=True),
            Case(r"ok", string=r"// OK", expected=False),
            # Patterns don't need to be escaped
            Case(re.compile(r"."), string=r"// x", expected=True),
            # Pattern flags apply
            Case(re.compile(r"a"), string=r"// A", expected=False),
            Case(
                re.compile(r"a", flags=re.IGNORECASE),
                string=r"// A",
                expected=True,
            ),
        ):
            with self.subTest(c):
                assertExpected = (
                    self.assertTrue if c.expected else self.assertFalse
                )
                assertExpected(retools.comment(c.pattern).search(c.string))

    def test_not_string(self):
        class Case(NamedTuple):
            pattern: Union[Pattern, str]
            string: str
            expected: bool

        for c in (
            # Single-quoted string
            Case(r"ok", string=r"'' ok", expected=True),
            Case(r"ok", string=r"'ok'", expected=False),
            Case(r"ok", string=r"'ok", expected=False),
            # Backslash escaping
            Case(r"ok", string=r"'\''ok", expected=True),
            Case(r"ok", string=r"'\\'ok", expected=True),
            Case(r"ok", string=r"'\\\'ok", expected=False),
            # Double-quoted string aren't strings in Apex
            Case(r"ok", string=r'"ok"', expected=True),
        ):
            with self.subTest(c):
                assertExpected = (
                    self.assertTrue if c.expected else self.assertFalse
                )
                assertExpected(retools.not_string(c.pattern).search(c.string))


class TestTermInfo(unittest.TestCase):
    @staticmethod
    def fields() -> Iterable[str]:
        return terminfo.TermInfo.__annotations__.keys()

    def test_get(self):
        self.assertEqual(terminfo.TermInfo.get(color=False), terminfo.DumbTerm)
        self.assertEqual(terminfo.TermInfo.get(color=True), terminfo.AnsiTerm)

    def test_dumb_term(self):
        """Ensure DumbTerm only contains blank color codes."""
        for field in self.fields():
            with self.subTest(field):
                self.assertEqual(getattr(terminfo.DumbTerm, field), "")

    def test_ansi_term(self):
        """Ensure AnsiTerm has defined all color codes."""
        for field in self.fields():
            with self.subTest(field):
                self.assertNotEqual(getattr(terminfo.AnsiTerm, field), "")


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)  # Tests shouldn't spew logs
    unittest.main()
