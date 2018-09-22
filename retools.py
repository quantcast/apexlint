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
