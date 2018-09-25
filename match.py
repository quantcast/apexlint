import contextlib
import logging
import os
import pathlib
import re
from typing import Iterable, Iterator, Union, Sequence, Type

from . import PROGNAME, base, pathtools, retools

log = logging.getLogger(__name__)

NOQA = retools.comment(re.compile("noqa", flags=re.IGNORECASE))


def files(
    paths: Iterable[pathlib.Path],
    *,
    suppress: bool = True,
    validators: Sequence[Type[base.Validator]],
) -> Iterator[Union[Exception, base.Message]]:
    """Return a Message iterator, as returned by `validators` for `paths`."""
    for path in paths:
        filename = os.fspath(path)
        log.debug(f"Validating: {filename}")

        enabled = base.Validator.filter(validators, path=path)
        if not enabled:
            continue

        with contextlib.ExitStack() as stack:
            try:
                f = path.open(mode="r")
                if not pathtools.StdIn.typeof(path):
                    stack.enter_context(f)
            except IOError as e:
                log.error(f"{PROGNAME}: {e}")
                yield e
                continue

            yield from lines(
                f, path=path, suppress=suppress, validators=enabled
            )


def lines(
    lines: Iterable[str],
    *,
    path: pathlib.Path,
    suppress: bool = True,
    validators: Sequence[Type[base.Validator]],
) -> Iterator[base.Message]:
    """Return a Message iterator, as returned by `validators` for `lines`."""

    enabled = base.Validator.filter(validators, path=path)
    if not enabled:
        return

    for lineno, line in enumerate(lines, start=1):
        if suppress and NOQA.search(line):
            continue

        for v in validators:
            for error in v.errors(line, suppress=suppress):
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
    suppress: bool = True,
    validators: Sequence[Type[base.Validator]],
    verbose: int = 0,
) -> Iterator[Union[Exception, str]]:
    for message in files(paths, suppress=suppress, validators=validators):
        if isinstance(message, Exception):
            yield message
            continue
        yield message.render(verbose=verbose)
