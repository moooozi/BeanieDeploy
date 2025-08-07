from typing import List, Dict, Any, Type

from models.page import Page

SpinDictList = List[Dict[str, Any]]

NavigationFlow = Dict[Type[Page], Dict[str, Any]]
