import operator
from typing import AbstractSet, Iterable, Type

from . import base, retools


def library(
    *,
    select: AbstractSet[str] = frozenset(),
    ignore: AbstractSet[str] = frozenset(),
) -> Iterable[Type[base.Validator]]:
    """Return a tuple of all Validator implementations"""
    enabled = base.Validator.__subclasses__()
    if select:
        enabled = [v for v in enabled if v.__name__ in select]
    if ignore:
        enabled = [v for v in enabled if v.__name__ not in ignore]
    return tuple(sorted(enabled, key=operator.attrgetter("__name__")))


def names() -> Iterable[str]:
    """Return a tuple of all Validator names"""
    return tuple(v.__name__ for v in library())
