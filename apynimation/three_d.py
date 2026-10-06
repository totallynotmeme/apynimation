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

        # shift point to camera-space
        pos3d = self.pos3d - self.camera.pos
        # rotate point if needed
        if self.camera.rot.z != 0:
            pos3d.rotate_z_ip(self.camera.rot.z)
        if self.camera.rot.x != 0:
            pos3d.rotate_y_ip(self.camera.rot.x)
        if self.camera.rot.y != 0:
            pos3d.rotate_x_ip(self.camera.rot.y)

        # check if we can project the point
        if pos3d.z <= 0:
            self.valid = False
            return

        # if the point is valid, pre-compute its projected position
        self.x = pos3d.x
        self.y = pos3d.y
        self *= self.camera.focal_length / pos3d.z
        # moving (0, 0) to the center of the screen
        self.x += Window.res[0] / 2
        self.y += Window.res[1] / 2
        self.valid = True


class Camera:
    def __init__(self, pos=None, focal_length=250):
        self.pos = pos or Vector3()
        self.rot = Vector3()
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
