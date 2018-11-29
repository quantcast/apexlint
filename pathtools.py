import contextlib
import logging
import os
import pathlib
import sys
from typing import IO, Iterable, Iterator, Set

log = logging.getLogger(__name__)


class StdIn(pathlib.Path):
    """Represent standard input as a pathlib.Path."""

    STDIN_FILENO = sys.stdin.fileno()
    _flavour = None
    _cparts = ()
    _parts = ()

    def __new__(cls, *args, **kwargs):
        # Suppress pathlib.Path.__new__()
        self = object.__new__(cls)
        self.__init__(*args, **kwargs)
        return self

    def __init__(self, stream: IO = sys.stdin) -> None:
        self.stream = stream

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return "<stdin>"

    def is_dir(self) -> bool:
        return False

    def open(self, *args, **kwargs):
        if self.stream.closed and self.stream.name == "<stdin>":
            self.stream = os.fdopen(self.STDIN_FILENO)
        return self.stream

    def resolve(self, *args, **kwargs):
        return self

    @classmethod
    def typeof(cls, instance) -> bool:
        return isinstance(instance, cls)


stdin = StdIn()


@contextlib.contextmanager
def chdir(path):
    curdir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(curdir)


def paths(files: Iterable[str]) -> Iterator[pathlib.Path]:
    """Convert filenames into pathlib.Path instances."""
    yield from (pathlib.Path(f) if f != "-" else stdin for f in files)


def unique(paths: Iterable[pathlib.Path]) -> Iterator[pathlib.Path]:
    """Return an object that filters out duplicate paths."""
    seen: Set[pathlib.Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            yield path


def walk(paths: Iterable[pathlib.Path]) -> Iterator[pathlib.Path]:
    """Return an object that produces all recursive files in paths."""
    for path in paths:
        if path.is_dir():
            yield from (p for p in path.rglob("*") if not p.is_dir())
            continue

        yield path
