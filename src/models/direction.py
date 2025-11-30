"""
Text direction handling for RTL/LTR language support.
Provides mapping of directional terms that flip for right-to-left languages.
"""


class Direction:
    """
    Manages text direction mappings for UI layouts.

    For RTL languages, directional properties are automatically flipped.
    For example, 'west' becomes 'east', 'left' becomes 'right', etc.
    """

    def __init__(self, is_right_to_left: bool = False):
        """
        Initialize direction handler.

        Args:
            is_right_to_left: Whether this is an RTL language
        """
        self.is_right_to_left = is_right_to_left

        # Initialize direction mappings
        if is_right_to_left:
            # RTL: flip all horizontal directions
            self.w = "e"
            self.e = "w"
            self.ne = "nw"
            self.nw = "ne"
            self.se = "sw"
            self.sw = "se"
            self.nse = "nsw"
            self.nsw = "nse"
            self.l = "right"
            self.r = "left"
        else:
            # LTR: standard directions
            self.w = "w"
            self.e = "e"
            self.ne = "ne"
            self.nw = "nw"
            self.se = "se"
            self.sw = "sw"
            self.nse = "nse"
            self.nsw = "nsw"
            self.l = "left"
            self.r = "right"
