# /apynimation/ui.py
# includes interactive components for a user interface
# v0.0.0-indev  /  use current commit as the version

import pygame as pg
from . import Input


class Theme:
    def __init__(self, base):
        self.color = base

    def __repr__(self):
        return f"<{self.__class__.__name__} base={self.base}>"

    @property
    def color(self):
        return self.base

    @color.setter
    def color(self, val):
        self.base = pg.Color(val)
        h, s, v, a = self.base.hsva
        self.bright = pg.Color(0)
        self.bright.hsva = (h, s, min(v + 10, 100), a)
        self.dark = pg.Color(0)
        self.dark.hsva = (h, s, max(v - 10, 0), a)

default_theme = Theme((0, 75, 150))


STATE_IDLE = 0
STATE_HOVERING = 1
STATE_HOLDING = 2

class Button:
    rect_width = 0
    rect_corner_args = (5,)

    def __init__(self, pos, size, theme=default_theme):
        self.pos = pos
        self.size = size
        self.theme = theme
        self.state = STATE_IDLE
        self.color = self.theme.base
        self.rect = pg.Rect(self.pos, self.size)

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.pos}>"

    def step(self, t=0):
        self.rect.update(self.pos, self.size)

        if Input.mouse_just_pressed[0]:
            if self.rect.collidepoint(Input.mouse_pos):
                self.state = STATE_HOLDING
                self.color = self.theme.dark
            return

        if self.state == STATE_HOLDING and Input.mouse_just_released[0]:
            if self.rect.collidepoint(Input.mouse_pos):
                self.callback()

        if not Input.mouse_buttons[0]:
            if self.rect.collidepoint(Input.mouse_pos):
                self.state = STATE_HOVERING
                self.color = self.theme.bright
            else:
                self.state = STATE_IDLE
                self.color = self.theme.base

    def draw(self, target):
        pg.draw.rect(target, self.color, self.rect, self.rect_width, *self.rect_corner_args)

    # default callback function, should be overwritten (button.callback = ...)
    def callback(self):
        print(f"Undefined callback function for {self}")
