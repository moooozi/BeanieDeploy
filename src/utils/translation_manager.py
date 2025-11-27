"""
Modern localization using babel's gettext.
Provides GNU gettext-based internationalization.
"""
import gettext as gettext_module
from pathlib import Path
from typing import Optional, Union


# Locate the locales directory
_LOCALES_DIR = Path(__file__).parent.parent / "locales"


class TranslationManager:
    """Manages translations using babel/gettext."""
    
    def __init__(self, domain: str = "messages", locales_dir: Optional[Path] = None):
        """
        Initialize translation manager.
        
        Args:
            domain: Translation domain (default: "messages")
            locales_dir: Path to locales directory (default: src/locales)
        """
        self.domain = domain
        self.locales_dir = locales_dir or _LOCALES_DIR
        self._current_language = "en"
        self._translation = self._load_translation(self._current_language)
    
    def _load_translation(self, language_code: str) -> Union[gettext_module.GNUTranslations, gettext_module.NullTranslations]:
        """
        Load gettext translations for specified language.
        
        Args:
            language_code: Language code (e.g., 'en', 'de', 'ar')
            
        Returns:
            GNUTranslations object or NullTranslations fallback
        """
        try:
            return gettext_module.translation(
                self.domain,
                localedir=str(self.locales_dir),
                languages=[language_code],
                fallback=False
            )
        except FileNotFoundError:
            # Fallback to NullTranslations if no .mo file exists
            if language_code != "en":
                print(f"Translation for '{language_code}' not found, using fallback")
            return gettext_module.NullTranslations()
    
    def set_language(self, language_code: str) -> None:
        """
        Change the active language.
        
        Args:
            language_code: Language code (e.g., 'en', 'de', 'ar')
        """
        self._current_language = language_code
        self._translation = self._load_translation(language_code)
    
    def get_language(self) -> str:
        """Get current language code."""
        return self._current_language
    
    def gettext(self, message: str) -> str:
        """
        Translate a message.
        
        Args:
            message: Message to translate
            
        Returns:
            Translated message
        """
        return self._translation.gettext(message)
    
    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """
        Translate a message with plural forms.
        
        Args:
            singular: Singular form
            plural: Plural form
            n: Count for determining plural form
            
        Returns:
            Translated message in appropriate form
        """
        return self._translation.ngettext(singular, plural, n)
    
    def pgettext(self, context: str, message: str) -> str:
        """
        Translate with context (requires pgettext support).
        
        Args:
            context: Message context
            message: Message to translate
            
        Returns:
            Translated message
        """
        # Use context separator for disambiguation
        contextualized = f"{context}\x04{message}"
        translated = self._translation.gettext(contextualized)
        
        # If translation not found, return original message without context
        if translated == contextualized:
            return message
        return translated


# Global singleton instance
_manager = TranslationManager()


def set_language(language_code: str) -> None:
    """Set the application language."""
    _manager.set_language(language_code)


def get_language() -> str:
    """Get current language code."""
    return _manager.get_language()


def gettext(message: str) -> str:
    """Translate a message (shorthand)."""
    return _manager.gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Translate with plural forms (shorthand)."""
    return _manager.ngettext(singular, plural, n)


def pgettext(context: str, message: str) -> str:
    """Translate with context (shorthand)."""
    return _manager.pgettext(context, message)


# Common alias for gettext
_ = gettext
