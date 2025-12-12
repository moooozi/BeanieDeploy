"""
Compatibility check types and data structures.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CheckType(Enum):
    ARCH = "arch"
    UEFI = "uefi"
    RAM = "ram"
    SPACE = "space"
    RESIZABLE = "resizable"
    EFI_SPACE = "efi_space"
    GPT = "gpt"

    @property
    def weight(self):
        weights = {
            CheckType.RESIZABLE: 30,
        }
        return weights.get(self, 10)


@dataclass
class Check:
    name: str
    result: Any
    returncode: int | None


class DoneChecks:
    def __init__(self):
        self.checks: dict[CheckType, Check] = {
            check_type: Check(name=check_type.value, result=None, returncode=None)
            for check_type in CheckType
        }
