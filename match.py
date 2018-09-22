import pathlib
from typing import Iterable, Iterator, Sequence, Type

from . import base


def lines(
    lines: Iterable[str],
    *,
    path: pathlib.Path,
    validators: Sequence[Type[base.Validator]],
) -> Iterator[base.Message]:
    for lineno, line in enumerate(lines, start=1):
        for v in validators:
            for error in v.errors(line):
                yield base.Message(
                    location=base.Location(
                        path=path, line=lineno, match=error.match
                    ),
                    message=error.message,
                )
