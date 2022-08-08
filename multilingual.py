available_languages = {
    # 'display name': ('codename(filename)', 'is right-to-left?'
    'العربية': ('ar', 1),
    'English': ('en', 0),
    'Deutsch': ('de', 0),
}


def right_to_left_lang(is_true):
    """invert default directions. This enables support for 'right-to-left' written languages, can be reverted by setting
    the input variable to False
    :rtype: dictionary with the new directions"""
    if is_true:
        return {"w": "e", "e": "w", "ne": "nw", "se": "sw", "sw": "se", "nw": "ne", "l": "right", "r": "left"}
    else:
        return {"w": "w", "e": "e", "ne": "ne", "se": "se", "sw": "sw", "nw": "nw", "l": "left", "r": "right"}


def change_lang(new_lang):
    """Used to change GUI's display language"""
    from importlib import import_module
    lang_new = available_languages[new_lang]
    ln = import_module('.' + lang_new[0], 'translations')
    DI_VAR = right_to_left_lang(lang_new[1])
    return DI_VAR, ln



