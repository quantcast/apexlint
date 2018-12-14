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
import re
from typing import Optional, Pattern, Union

PatternOrStr = Union[str, Pattern]


def escape(s: PatternOrStr, flags: Optional[int] = None) -> Pattern:
    """Return Pattern object for `s`, escaping it if necessary.
    If `flags` is not None, clobber any flags on `s`.
    """
    if isinstance(s, Pattern):
        if flags is not None:
            s = re.compile(s.pattern, flags=flags)
        return s

    return re.compile(re.escape(s), flags=(flags or 0))


def comment(s: PatternOrStr) -> Pattern:
    """Return Pattern object that matches `s` inside a comment."""
    pattern = escape(s)
    return not_string(
        fr"""
        (?x:                   # Match s inside a comment
            /\*                # C-style /* comment */
            (\*(?!\/)|[^*])*?  # Ignore closing */
            (?-x:(?P<c>{pattern.pattern}))
            .*?
            \*/
        |
            //                 # C++-style // comment
            .*?
            (?-x:(?P<cpp>{pattern.pattern}))
        )
        """.strip(),
        flags=pattern.flags,
    )


def not_string(s: PatternOrStr, flags: int = 0) -> Pattern:
    """Return Pattern object that matches `s` outside quoted strings."""
    if isinstance(s, Pattern):
        flags = s.flags
        s = str(s.pattern)

    return re.compile(
        fr"""
        (?x:                   # Ensure we are outside a single-quoted string
            ^
            (?:                # Match pairs of single-quotes
                [^']*
                '
                (?:
                    \\\\       # Quoted backslash: \\
                |
                    \\'        # Quoted apostrophe: \'
                |
                    [^'\\]     # Not the ending quote or a dangling backslash
                )*
                '
            )*
            [^']*
        )
        """.strip()
        + s,
        flags=flags,
    )
