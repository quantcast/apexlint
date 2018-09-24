import contextlib
import logging
import os
import pathlib
from typing import Iterable, Iterator, Sequence, Type

from . import base, pathtools

log = logging.getLogger(__name__)


def files(
    paths: Iterable[pathlib.Path],
    *,
    validators: Sequence[Type[base.Validator]],
) -> Iterator[base.Message]:
    """Return a Message iterator, as returned by `validators` for `paths`."""
    for path in paths:
        filename = os.fspath(path)
        log.debug(f"Validating: {filename}")

        enabled = base.Validator.filter(validators, path=path)
        if not enabled:
            continue

        with contextlib.ExitStack() as stack:
            f = path.open(mode="r")
            if not pathtools.StdIn.typeof(path):
                stack.enter_context(f)

            yield from lines(f, path=path, validators=enabled)


def lines(
    lines: Iterable[str],
    *,
    path: pathlib.Path,
    validators: Sequence[Type[base.Validator]],
) -> Iterator[base.Message]:
    """Return a Message iterator, as returned by `validators` for `lines`."""

    enabled = base.Validator.filter(validators, path=path)
    if not enabled:
        return

    for lineno, line in enumerate(lines, start=1):
        for v in validators:
            for error in v.errors(line):
                yield base.Message(
                    location=base.Location(
                        path=path, line=lineno, match=error.match
                    ),
                    message=error.message,
                    source=error.source,
                )


def render(
    paths: Iterable[pathlib.Path],
    *,
    validators: Sequence[Type[base.Validator]],
    verbose: int = 0,
) -> Iterator[str]:
    for m in files(paths, validators=validators):
        yield m.render(verbose=verbose)
