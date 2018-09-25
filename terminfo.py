import abc
from typing import Type


class TermInfo(abc.ABC):
    BOLD: str
    BOLD_RED: str
    GRAY: str
    RED: str
    RESET: str

    @staticmethod
    def get(*, color: bool) -> Type["TermInfo"]:
        return AnsiTerm if color else DumbTerm


class DumbTerm(TermInfo):
    BOLD: str = ""
    BOLD_RED: str = ""
    GRAY: str = ""
    RED: str = ""
    RESET: str = ""


class AnsiTerm(TermInfo):
    BOLD: str = "\033[1m"
    BOLD_RED: str = "\033[1;31m"
    GRAY: str = "\033[0;33m"
    RED: str = "\033[0;31m"
    RESET: str = "\033[0m"
