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
        return {"w": "e", "ne": "nw", "se": "sw", "sw": "se", "nw": "ne", "l": "right", "r": "left"}
    else:
        return {"w": "w", "ne": "ne", "se": "se", "sw": "sw", "nw": "nw", "l": "left", "r": "right"}
