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
