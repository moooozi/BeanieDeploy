from typing import List, Dict, Any, Type

# Import Page using TYPE_CHECKING to avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from models.page import Page

SpinDictList = List[Dict[str, Any]]

# Use string annotation to avoid runtime import
NavigationFlow = Dict[Type["Page"], Dict[str, Any]]
