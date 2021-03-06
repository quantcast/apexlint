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
import abc
import os
import pathlib
import textwrap
from typing import (
    Iterable,
    Match,
    NamedTuple,
    Optional,
    Pattern,
    Sequence,
    Tuple,
    Type,
)

from . import pathtools, terminfo


class Error(NamedTuple):
    match: Match
    message: str


class Location(NamedTuple):
    line: int
    match: Match
    path: pathlib.Path

    @property
    def len(self) -> int:
        try:
            start, end = self.match.span("cursor")
        except IndexError:
            return 0
        return max(end - start, 0)

    @property
    def column(self) -> int:
        try:
            return self.match.start("cursor")
        except IndexError:
            return self.match.start()

    @property
    def arrow(self) -> str:
        indent = " " * self.column
        arrow = "^" + "~" * (self.len - 1)
        return indent + arrow

    def __str__(self):
        filename = os.fspath(self.path)
        return f"{filename}:{self.line}:{self.column}"


class Message(NamedTuple):
    location: Location
    message: str
    source: str

    def split_message(self) -> Tuple[str, Optional[str]]:
        bits = self.message.split("\n", 1)
        if len(bits) > 1:
            return bits[0], bits[1]
        return bits[0], None

    def render(
        self,
        *,
        indent: int = 1,
        term: Optional[Type[terminfo.TermInfo]] = None,
        verbose: int = 0,
    ) -> str:
        if term is None:
            term = terminfo.TermInfo.get(color=False)

        summary, description = self.split_message()

        out = (
            f"{term.BOLD}{self.location}: {term.BOLD_RED}error:{term.RESET} "
            f"{summary}"
        )

        if verbose > 0 and description:
            out += (
                "\n"
                + term.GRAY
                + textwrap.indent(description, prefix=" " * indent * 2)
                + term.RESET
            )

        if verbose >= 0:
            out += "\n" + textwrap.indent(
                (
                    f"{self.source}\n"
                    f"{term.RED}{self.location.arrow}{term.RESET}"
                ),
                prefix=" " * indent,
            )

        return out

    def __str__(self):
        return self.render()


class Validator(abc.ABC):
    """Define a validator to run against a source file:
    `invalid` is a regexp that matches errors in the file.
    `filenames` is a sequence of wildcard patterns for files to match.
    `suppress` is a regexp that silences an error if it matches.
    """

    invalid: Pattern
    filenames: Iterable[str] = ("*.cls", "*.trigger")
    suppress: Optional[Pattern] = None

    @classmethod
    def enabled(cls, *, path: pathlib.Path):
        return (
            pathtools.StdIn.typeof(path)
            or bool(cls.filenames)
            and any(path.match(pattern) for pattern in cls.filenames)
        )

    @staticmethod
    def filter(
        validators: Iterable[Type["Validator"]], *, path: pathlib.Path
    ) -> Sequence[Type["Validator"]]:
        return tuple(
            v
            for v in validators
            if pathtools.StdIn.typeof(path) or v.enabled(path=path)
        )

    @classmethod
    def errors(cls, line: str, *, suppress: bool) -> Iterable[Error]:
        if suppress and cls.suppress is not None and cls.suppress.search(line):
            return

        for m in cls.invalid.finditer(line):
            yield Error(match=m, message=cls.message(match=m, source=line))

    @classmethod
    def message(cls, *, match: Match, source: str) -> str:
        if not cls.__doc__:
            return ""

        # Dedent the description
        bits = cls.__doc__.split("\n", 1)
        msg = bits[0]
        if len(bits) > 1:
            msg += "\n" + textwrap.dedent(bits[1])

        return msg.format(match=match, source=source).strip()
