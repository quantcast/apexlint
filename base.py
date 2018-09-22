import abc
import os
import pathlib
from typing import Iterable, Match, NamedTuple, Pattern


class Error(NamedTuple):
    match: Match
    message: str
    source: str


class Location(NamedTuple):
    line: int
    match: Match
    path: pathlib.Path

    @property
    def column(self) -> int:
        try:
            return self.match.start("cursor")
        except IndexError:
            return self.match.start()

    def __str__(self):
        filename = os.fspath(self.path)
        return f"{filename}:{self.line}:{self.column}"


class Message(NamedTuple):
    location: Location
    message: str

    def render(self, *, indent: int = 1) -> str:
        return f"{self.location}: error: {self.message}"

    def __str__(self):
        return self.render()


class Validator(abc.ABC):
    """Define a validator to run against a source file:
    `invalid` is a regexp that matches errors in the file.
    """

    invalid: Pattern

    @classmethod
    def errors(cls, line: str) -> Iterable[Error]:
        for m in cls.invalid.finditer(line):
            source = line.rstrip("\n")
            yield Error(
                match=m,
                message=cls.message(match=m, source=source),
                source=source,
            )

    @classmethod
    def message(cls, *, match: Match, source: str) -> str:
        if not cls.__doc__:
            return ""

        return cls.__doc__.format(match=match, source=source).strip()
