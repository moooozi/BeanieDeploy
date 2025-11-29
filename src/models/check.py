"""
Compatibility check types and data structures.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class CheckType(Enum):
    ARCH = "arch"
    UEFI = "uefi"
    RAM = "ram"
    SPACE = "space"
    RESIZABLE = "resizable"
    EFI_SPACE = "efi_space"


@dataclass
class Check:
    name: str
    result: Any
    returncode: Optional[int]
    process: Optional[Any]


class DoneChecks:
    def __init__(self):
        self.checks: Dict[CheckType, Check] = {
            check_type: Check(
                name=check_type.value, result=None, returncode=None, process=None
            )
            for check_type in CheckType
        }