import importlib
from types import SimpleNamespace
language_list = {
    # 'display name': ('codename(filename)', 'is right-to-left?'
    'العربية': ('ar', 1),
    'English': ('en', 0),
    'Deutsch': ('de', 0),
}


def right_to_left_lang(is_true):
    """changes all objects alignments from left to right if false, and vice versa if true. This enables support for
right-to-left languages"""
    if is_true:
        return {"w": "e", "e": "w", "ne": "nw", "se": "sw", "sw": "se", "nw": "ne", "l": "right", "r": "left"}
    else:
        return {"w": "w", "e": "e", "ne": "ne", "se": "se", "sw": "sw", "nw": "nw", "l": "left", "r": "right"}


def change_lang(new_lang):
    """Used to change GUI's display language"""
    lang_new = language_list[new_lang]
    ln = importlib.import_module('.' + lang_new[0], 'translations')
    directions = right_to_left_lang(lang_new[1])
    return directions, ln



