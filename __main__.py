import argparse
import functools
import itertools
import logging
import multiprocessing.pool
import pathlib
import sys
from typing import IO, Iterable, Optional, Sequence, Tuple, Type

from . import validators  # import validators to register them
from . import PROGNAME, base, match, pathtools, terminfo

log = logging.getLogger(__name__)


def render_parallel(
    paths: Iterable[pathlib.Path],
    *,
    pool: Optional[multiprocessing.pool.Pool],
    **kwargs,
):
    if not pool:
        return match.render(paths, **kwargs)

    return itertools.chain.from_iterable(
        pool.imap(functools.partial(render, **kwargs), ((p,) for p in paths))
    )


def render(*args, **kwargs):
    return list(match.render(*args, **kwargs))


def lint(
    paths: Iterable[pathlib.Path],
    *,
    jobs: Optional[int] = None,
    output: Optional[IO] = sys.stdout,
    output_count: Optional[IO] = None,
    suppress: bool = True,
    term: Optional[Type[terminfo.TermInfo]] = None,
    validators: Sequence[Type[base.Validator]],
    verbose: int = 0,
) -> Tuple[Iterable[str], Iterable[Exception]]:
    messages = []
    errors = []

    with multiprocessing.Pool(jobs) as pool:
        for message in render_parallel(
            paths,
            pool=(pool if jobs != 1 else None),
            suppress=suppress,
            term=term,
            validators=validators,
            verbose=verbose,
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
        jobs=config.jobs,
        output_count=sys.stderr if config.count else None,
        suppress=config.suppress,
        term=terminfo.TermInfo.get(color=config.color),
        validators=tuple(
            validators.library(
                select=frozenset(config.select),
                ignore=frozenset(config.ignore),
            )
        ),
        verbose=config.verbose,
    )
    if messages:
        return 1
    if errors:
        return 2
    return 0


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    validator_names = validators.names()

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

    class ColorAction(argparse.Action):
        def __call__(self, parser, namespace, values, *args, **kwargs):
            namespace.color = self.parse(values)

        @staticmethod
        def parse(values):
            if values == "never":
                return False
            if values == "always":
                return True
            if values == "auto":
                return sys.stdout.isatty()

    parser.add_argument(
        "--color",
        action=ColorAction,
        choices=("always", "auto", "never"),
        default=ColorAction.parse("auto"),
        metavar="WHEN",
        help=("colorize the output; WHEN can be 'always', 'auto', or 'never'"),
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
        "--ignore",
        action="append",
        choices=validator_names,
        default=[],
        metavar="VALIDATOR",
        help="list of errors to ignore (default: none)",
    )

    parser.add_argument(
        "-j",
        "--jobs",
        default=None,
        metavar="N",
        type=int,
        help="number of parallel checks (default: number of CPUs)",
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
        "--select",
        action="append",
        choices=validator_names,
        default=[],
        metavar="VALIDATOR",
        help="list of errors to enable (default: all)",
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
