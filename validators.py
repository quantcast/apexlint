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
import operator
import re
from typing import AbstractSet, Iterable, Type

from . import base, retools


BASE_TYPES = r"""
           (
               (System\.)?  # Base types are in System namespace
               (
                   Blob
                   | Boolean
                   | Date
                   | DateTime
                   | Decimal
                   | Double
                   | Id
                   | Integer
                   | Long
                   | String
                   | Time
                   | Type
               )
           |
               (Schema\.)?  # SObject schema namespace
               (SObjectField|SObjectType)
           )
           """


class NoObjectMapKeys(base.Validator):
    """Map key might be mutable
    See https://github.com/quantcast/apexlint/blob/master/MAPS-AND-SETS.md
    """

    invalid = retools.not_string(
        fr"""
        \b
        new\s+ (?:Map)\s*<\s*     # "new Map<"
        (?!{ BASE_TYPES })      # Exclude these valid base types
        (?P<cursor>          # Capture key name
            .+?
        )
        \s*\,                # Type ends with comma
        """,
        flags=(re.IGNORECASE | re.VERBOSE),
    )
    suppress = retools.comment(
        "https://github.com/quantcast/apexlint/blob/master/MAPS-AND-SETS.md"
    )


class NoObjectSetMembers(base.Validator):
    """Set member might be mutable
    See https://github.com/quantcast/apexlint/blob/master/MAPS-AND-SETS.md
    """

    invalid = retools.not_string(
        fr"""
        \b
        new\s+ (?:Set)\s*<\s*     # "new Set<"
        (?!{ BASE_TYPES })      # Exclude these valid base types
        (?P<cursor>          # Capture member name
            .+?
        )
        \s*>                 # Type ends with angle bracket
        """,
        flags=(re.IGNORECASE | re.VERBOSE),
    )
    suppress = retools.comment(
        "https://github.com/quantcast/apexlint/blob/master/MAPS-AND-SETS.md"
    )


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
            @\s*future
        )
        """,
        flags=(re.IGNORECASE | re.VERBOSE),
    )


class NoSeeAllData(base.Validator):
    """SeeAllData used in @isTest
    The use of SeeAllData is forbidden because:
      1. Row-locking conflicts can cause processes and deployments to fail.
      2. It prevents concurrent test execution.
      3. SeeAllData=false doesn't do anything in classes where SeeAllData=true.
    """

    invalid = retools.not_string(
        r"""
        @\s*isTest
        \s*\(
        [^)]*
        (?P<cursor>              # Capture SeeAllData=true
            \b
            SeeAllData
            \s*=
            .*?
        )
        \s*
        [,)]
        """,
        flags=(re.IGNORECASE | re.VERBOSE),
    )


class NoTestMethod(base.Validator):
    """testMethod used instead of @isTest"""

    invalid = re.compile(
        r"""
        \b
        (?P<cursor>
            testMethod
        )
        \b
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
