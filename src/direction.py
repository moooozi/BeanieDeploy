class Direction:
    def __init__(self, is_right_to_left=False):
        self.is_right_to_left = is_right_to_left
        self._set_directions(is_right_to_left)

    def _set_directions(self, is_right_to_left):
        if is_right_to_left:
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
