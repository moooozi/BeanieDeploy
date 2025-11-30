# Import Page using TYPE_CHECKING to avoid circular import
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from models.page import Page

SpinDictList = list[dict[str, Any]]

# Use string annotation to avoid runtime import
NavigationFlow = dict[type["Page"], dict[str, Any]]
