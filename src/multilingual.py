current_lang = 'English'

available_languages = {
    # 'display name': ('codename(filename)', 'is right-to-left?'
    
    #'العربية': ('ar', 1),
    'English': ('en', 0),
    'Deutsch': ('de', 0),
}

def get_lang_by_code(code):
    for lang, values in available_languages.items():
        if values[0] == code:
            return lang
    return None

def right_to_left_lang(is_true):
    """invert default directions. This enables support for 'right-to-left' written languages, can be reverted by setting
    the input variable to False
    :rtype: dictionary with the new directions"""
    if is_true:
        return {"w": "e", "e": "w",
                "ne": "nw", "nw": "ne",
                "se": "sw", "sw": "se",
                "nse": "nsw", "nsw": "nse",
                "l": "right", "r": "left"}
    else:
        return {"w": "w", "e": "w",
                "ne": "ne", "nw": "nw",
                "se": "se", "sw": "sw",
                "nse": "nse", "nsw": "nsw",
                "l": "left", "r": "right"}


def set_lang(new_lang):
    """Used to change GUI's display language"""
    from importlib import import_module
    lang_new = available_languages[new_lang]
    global LN, DI_VAR
    LN = import_module('.' + lang_new[0], 'translations')
    DI_VAR = right_to_left_lang(lang_new[1])
    global current_lang
    current_lang = new_lang
    return DI_VAR, LN

def get_current_lang():
    return current_lang

def get_lang():
    return LN

def get_di_var():
    return DI_VAR
