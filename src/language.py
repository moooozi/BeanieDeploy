from importlib import import_module
from direction import Direction


class Language:
    def __init__(self, name, code, is_right_to_left):
        self.name = name
        self.code = code
        self.is_right_to_left = is_right_to_left
        self.direction = Direction(is_right_to_left)
        self.translations = import_module("." + code, "translations")

    def get_direction(self):
        return self.direction

    def get_translations(self):
        return self.translations
