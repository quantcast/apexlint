import operator
import re
from typing import AbstractSet, Iterable, Type

from . import base, retools


class NoComplexMapKeys(base.Validator):
    """Map key is SObject or Object
    See http://go.corp.qc/salesforce-maps
    """

    invalid = retools.not_string(
        r"""
        \b
        new\s+Map\s*<\s*     # "new Map<"
        (?!                  # Exclude these valid base types
            (
                (System\.)?  # Base types are in System namespace
                (Id|String|Integer|Long|Decimal|Date|DateTime|Type)
            |
                (Schema\.)?  # SObject schema namespace
                (SObjectField|SObjectType)
            )
        )
        (?P<cursor>          # Capture key name
            .+?
        )
        \s*\,                # Type ends with comma
        """,
        flags=(re.IGNORECASE | re.VERBOSE),
    )
    suppress = retools.comment("http://go.corp.qc/salesforce-maps")


class NoFutureInTest(base.Validator):
    """@future used in test class
    The use of @future in Tests is forbidden because:
      1. Futures are scheduled in a small finite queue.
      2. If "Disable Parallel Test Execution" is off, this queue can get full.
    Use @testSetup instead of @future to avoid mixed DML issues.
    Use Test.startTest() and Test.stopTest() to avoid "Too Many SOQL Queries"
    """

    filenames = ("*Test.cls", "TestUtils.cls", "UnitTestFactory.cls")
    invalid = retools.not_string(
        r"""
        (?P<cursor>
            @future
        )
        """,
        flags=(re.IGNORECASE | re.VERBOSE),
    )


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
