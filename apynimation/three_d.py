# /apynimation/three_d.py
# handles most graphics and logic in 3D space
# v0.0.0-indev  /  use current commit as the version

from . import Window, Point, Line
from pygame import Vector3
import pygame as pg


def _project(pos3d, target2d, focal_length):
    # projects a Vector3() onto Vector2() screen coordinates
    target2d.x = pos3d.x
    target2d.y = pos3d.y
    target2d *= focal_length / pos3d.z
    # moving (0, 0) to the center of the screen
    target2d.x += Window.res[0] / 2
    target2d.y += Window.res[1] / 2


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
        self._local3d = self.pos3d - self.camera.pos
        # rotate point if needed
        if self.camera.rot.x != 0:
            self._local3d.rotate_y_ip(self.camera.rot.x)
        if self.camera.rot.y != 0:
            self._local3d.rotate_x_ip(self.camera.rot.y)
        if self.camera.rot.z != 0:
            self._local3d.rotate_z_ip(self.camera.rot.z)

        # check if we can project the point
        if self._local3d.z <= 0:
            self.valid = False
            return

        # if the point is valid, pre-compute its projected position
        _project(self._local3d, self, self.camera.focal_length)
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


class Line3d(Line):
    tmp_point = pg.Vector2() # used to split a line into 2

    def draw(self, target):
        if not self.p1.valid and not self.p2.valid:
            # line is completely off-screen
            return
        if self.p1.valid and self.p2.valid:
            # line is fully on-screen
            pg.draw.line(target, self.color, self.p1, self.p2, self.width)
            super().draw(target)
            return
        # line is partially on-screen
        # https://stackoverflow.com/questions/5666222/3d-line-plane-intersection
        # using p1 as projection camera (assuming p1.camera == p2.camera)
        camera = self.p1.camera
        normal = (0, 0, 1) # we're already in camera-space

        direction = self.p2._local3d - self.p1._local3d
        dot = direction.dot(normal)
        if abs(dot) < 0.01:
            # The segment is parallel to plane.
            return

        fac = -self.p1._local3d.dot(normal) / dot
        if fac < 0 or fac > 1:
            return

        # split_pos is (point) + direction * factor
        if self.p1.valid:
            point = self.p1
        else: # self.p2 has to be valid
            point = self.p2
            fac = fac - 1

        split_pos = point._local3d + direction * fac
        split_pos.z += 0.01 # near clipping distance
        _project(split_pos, Line3d.tmp_point, camera.focal_length)

        pg.draw.line(target, self.color, point, Line3d.tmp_point, self.width)
