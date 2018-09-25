import argparse
import logging
import pathlib
import sys
from typing import IO, Iterable, Optional, Sequence, Tuple, Type

from . import PROGNAME, base, match, pathtools

log = logging.getLogger(__name__)


def lint(
    paths: Iterable[pathlib.Path],
    *,
    output: Optional[IO] = sys.stdout,
    output_count: Optional[IO] = None,
    suppress: bool = True,
    validators: Sequence[Type[base.Validator]],
    verbose: int = 0,
) -> Tuple[Iterable[str], Iterable[Exception]]:
    messages = []
    errors = []

    for message in match.render(
        paths, suppress=suppress, validators=validators, verbose=verbose
    ):
        if isinstance(message, Exception):
            errors.append(message)
            continue

        messages.append(message)
        if output is not None:
            print(message, file=output)

    if output_count is not None:
        print(len(messages), file=output_count)

    return messages, errors


def main(
    config: argparse.Namespace,
    *,
    output: IO = sys.stdout,
    output_count: IO = sys.stderr,
):
    messages, errors = lint(
        pathtools.unique(pathtools.walk(pathtools.paths(config.files))),
        output_count=sys.stderr if config.count else None,
        suppress=config.suppress,
        validators=[],
        verbose=config.verbose,
    )
    if messages:
        return 1
    if errors:
        return 2
    return 0


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Salesforce code for common errors", prog=PROGNAME
    )

    parser.add_argument(
        "files",
        metavar="FILE",
        default=["-"],
        nargs="*",
        help="files to validate",
    )

    parser.add_argument(
        "--count",
        action="store_true",
        help="print total number of errors to standard error",
    )

    parser.add_argument(
        "--debug", action="count", default=0, help="debug output"
    )

    parser.add_argument(
        "--no-suppress",
        action="store_false",
        default=True,
        dest="suppress",
        help='disable the effect of "# noqa"; so suppression is ignored',
    )

    class QuietAction(argparse.Action):
        def __call__(self, parser, namespace, values, *args, **kwargs):
            namespace.verbose -= 1

    parser.add_argument(
        "-q",
        "--quiet",
        action=QuietAction,
        nargs=0,
        help="less verbose messages; see --verbose",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="more verbose messages",
    )

    return parser.parse_args(args)


if __name__ == "__main__":
    config = parse_args(sys.argv[1:])
    logging.basicConfig(
        level=logging.DEBUG if config.debug else logging.INFO,
        format=(("%(levelname)s: " if config.debug else "") + "%(message)s"),
        handlers=(logging.StreamHandler(),),
    )

    try:
        sys.exit(main(config))
    except KeyboardInterrupt as e:
        if config.debug:
            log.exception("")
        sys.exit(130)
    except Exception as e:
        log.exception(f"{PROGNAME}: {e}")
        sys.exit(3)
