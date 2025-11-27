"""
Language model for multi-language support.
"""
from dataclasses import dataclass
from importlib import import_module
from typing import Any
from models.direction import Direction


@dataclass
class Language:
    """
    Represents a language with its translations and text direction.
    
    Attributes:
        name: Display name of the language (e.g., "English", "Deutsch")
        code: ISO language code (e.g., "en", "de")
        is_right_to_left: Whether this language uses RTL text direction
    """
    name: str
    code: str
    is_right_to_left: bool
    
    def __post_init__(self):
        """Initialize derived attributes after dataclass initialization."""
        self.direction = Direction(self.is_right_to_left)
        self.translations = import_module("." + self.code, "translations")

    def get_direction(self) -> Direction:
        """Get the text direction for this language."""
        return self.direction

    def get_translations(self) -> Any:
        """Get the translation module for this language."""
        return self.translations
