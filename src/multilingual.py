"""
Modern multilingual support using babel gettext.
Follows standard gettext best practices with dotted key names.

Usage:
    from multilingual import _

    # Direct translation with IDE preview support
    title = _("btn.next")  # Hover shows: "Next"
    message = _("error.arch.0")  # Hover shows: "This device's CPU architecture is incompatible."

    # Named placeholders (babel best practice)
    text = _("total.download") % {"size": format_bytes(size)}
"""

from models.direction import Direction
from utils import translation_manager

# Expose standard gettext functions at module level
# The .pyi stub file provides type hints and preview tooltips for IDE
_ = translation_manager.gettext
gettext = translation_manager.gettext
ngettext = translation_manager.ngettext
pgettext = translation_manager.pgettext


# Language configuration: (code, display_name, is_rtl)
SUPPORTED_LANGUAGES = [
    ("en", "English", False),
    # Add more languages here as translations are added
    # ("de", "Deutsch", False),
    # ("ar", "العربية", True),
]


def get_supported_languages():
    """Get list of supported language display names."""
    return [lang[1] for lang in SUPPORTED_LANGUAGES]


def get_lang_code_by_name(display_name: str) -> str:
    """Get language code by display name."""
    for code, name, _ in SUPPORTED_LANGUAGES:
        if name == display_name:
            return code
    return "en"  # Default fallback


def get_lang_name_by_code(code: str) -> str:
    """Get display name by language code."""
    for lang_code, name, _ in SUPPORTED_LANGUAGES:
        if lang_code == code:
            return name
    return "English"  # Default fallback


def is_rtl_language(code: str) -> bool:
    """Check if language is right-to-left."""
    for lang_code, _, is_rtl in SUPPORTED_LANGUAGES:
        if lang_code == code:
            return is_rtl
    return False


def set_lang(language_name: str) -> tuple[Direction, None]:
    """
    Change the application language.

    Args:
        language_name: Display name (e.g., "English", "Deutsch")

    Returns:
        Tuple of (Direction, None) for backward compatibility
    """
    code = get_lang_code_by_name(language_name)
    translation_manager.set_language(code)

    is_rtl = is_rtl_language(code)
    direction = Direction(is_rtl)

    return direction, None


def get_current_language() -> str:
    """Get the current language code."""
    return translation_manager.get_language()


def get_di_var() -> Direction:
    """Get the current text direction."""
    code = translation_manager.get_language()
    is_rtl = is_rtl_language(code)
    return Direction(is_rtl)
