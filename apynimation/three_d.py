# /apynimation/three_d.py
# handles most graphics and logic in 3D space
# v0.0.0-indev  /  use current commit as the version

from pygame import Vector3
from . import Window, Point


class Point3d(Point):
    def __init__(self, *args, camera=None):
        self.pos3d = Vector3(*args)
        self.camera = camera or default_camera # default_camera defined lower
        self.prev_t = -1
        self.valid = False

        self.step() # to set self.x and self.y

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.pos3d}>"

    def step(self, t=0):
        # micro-optimization to prevent it from recomputing the same point 100 times
        if self.prev_t == t:
            return
        self.prev_t = t

        focal_len = self.camera.focal_length
        pos3d = self.pos3d - self.camera.pos
        if pos3d.z + focal_len <= 0:
            self.valid = False
            return

        # if the point is valid, pre-compute its screen position
        self.x = (pos3d.x * focal_len) / (pos3d.z + focal_len)
        self.y = (pos3d.y * focal_len) / (pos3d.z + focal_len)
        self.x += Window.res[0] / 2
        self.y += Window.res[1] / 2
        self.valid = True

    def draw(self, target):
        pass


class Camera:
    def __init__(self, pos=None, focal_length=250):
        self.pos = pos or Vector3()
        self.focal_length = focal_length

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.pos}>"

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, val):
        if isinstance(val, Point3d):
            val = val.pos3d
        self._pos = val

default_camera = Camera()
