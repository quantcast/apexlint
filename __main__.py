import argparse
import logging
import sys
from typing import IO, Sequence

from . import PROGNAME, match, pathtools

log = logging.getLogger(__name__)


def main(config: argparse.Namespace, *, output: IO = sys.stdout):
    for line in match.render(
        pathtools.unique(pathtools.walk(pathtools.paths(config.files))),
        validators=[],
        verbose=config.verbose,
    ):
        print(line, file=output)

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
        "--debug", action="count", default=0, help="debug output"
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
