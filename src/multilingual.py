from models.language import Language
from models.direction import Direction
from typing import Optional, Tuple
from types import ModuleType


# This file was written by 2. Semester me (kill me pls)

current_lang = "English"

available_languages = {
    # 'display name': ('codename(filename)', 'is right-to-left?'
    #'العربية': ('ar', 1),
    "English": ("en", 0),
    "Deutsch": ("de", 0),
}

current_language = Language("English", "en", False)


def get_lang_by_code(code: str) -> Optional[str]:
    for lang, values in available_languages.items():
        if values[0] == code:
            return lang
    return None


def set_lang(new_lang: str) -> Tuple[Direction, ModuleType]:
    """Used to change GUI's display language"""
    lang_new = available_languages[new_lang]
    global current_language
    current_language = Language(new_lang, lang_new[0], bool(lang_new[1]))
    global current_lang
    current_lang = new_lang
    return current_language.get_direction(), current_language.get_translations()


def get_lang():
    return current_language.get_translations()


def get_di_var():
    return current_language.get_direction()
