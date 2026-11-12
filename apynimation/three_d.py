# /apynimation/three_d.py
# handles most graphics and logic in 3D space
# v0.0.0-indev  /  use current commit as the version

from . import Window, Point, Line, Polygon
from pygame import Vector3
import pygame as pg


def _project(pos3d, target2d, focal_length):
    # projects a Vector3() onto Vector2() screen coordinates
    target2d.x = pos3d.x
    target2d.y = pos3d.y
    target2d *= focal_length / pos3d.z
    # moving (0, 0) to the center of the screen
    target2d += Window.center


class Point3d(Point):
    def __init__(self, *args, camera=None):
        self.pos3d = Vector3(*args)
        self.camera = camera or Camera3d.default
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
        if self._local3d.z <= 0.1:
            self.valid = False
            return

        # if the point is valid, pre-compute its projected position
        _project(self._local3d, self, self.camera.focal_length)
        self.valid = True


class Camera3d:
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

Camera3d.default = Camera3d()


# TODO: possibly make this a subclass of Container?
class Container3d:
    active = True # default

    def __init__(self):
        self.objects = []

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.objects)} objects>"

    def step(self, t=0):
        for i in self.objects:
            i.step(t)
        # sorting by z-depth
        self.objects.sort(key=lambda x: x._get_z_depth(), reverse=True)

    def draw(self, target):
        for i in self.objects:
            i.draw(target)

    def add(self, *objects):
        self.objects.extend(objects)
        if len(objects) == 1:
            return objects[0]
        return objects

    def remove(self, *objects):
        for obj in objects:
            if obj in self.objects:
                self.objects.remove(obj)


class Line3d(Line):
    split_point = pg.Vector2() # used to split the projected line

    def draw(self, target):
        if not self.p1.valid and not self.p2.valid:
            # line is completely off-screen
            return
        if self.p1.valid and self.p2.valid:
            # line is fully on-screen
            clipped = Window.rect.clipline(self.p1, self.p2)
            if not clipped:
                # actually it's not on screen
                #pg.draw.line(target, "red", self.p1, self.p2, 5)
                return
            pg.draw.line(target, self.color, *clipped, self.width)
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
        else: # p2 has to be valid
            point = self.p2
            fac = fac - 1

        split_pos = point._local3d + direction * fac
        split_pos.z += 0.01 # near clipping distance
        _project(split_pos, Line3d.split_point, camera.focal_length)

        clipped = Window.rect.clipline(point, Line3d.split_point)
        if not clipped:
            # line isn't even on screen and we did this for nothing
            #pg.draw.line(target, "green", point, Line3d.split_point, 5)
            return
        pg.draw.line(target, self.color, *clipped, self.width)


class Triangle3d(Polygon):
    check_normal = True # default
    normal_point = pg.Vector2() # temp

    def draw(self, target, _points=None):
        p1, p2, p3 = _points or self.points
        valid_count = p1.valid + p2.valid + p3.valid
        if valid_count == 0:
            # triangle not on screen at all
            return

        if self.check_normal:
            # check to not draw the back face
            a = p2 - p1
            b = (p3 - p2).rotate(90)
            if a.dot(b) >= 0:
                # triangle facing the wrong way
                return

        if valid_count == 3:
            # triangle is fully on screen
            pg.draw.polygon(target, self.color, self.points, self.width)
            return

        # TODO: clipping the triangle
        if p1.valid:
            p1.draw(target)
        if p2.valid:
            p2.draw(target)
        if p3.valid:
            p3.draw(target)

    def _get_z_depth(self):
        return (self.points[0]._local3d.z \
              + self.points[1]._local3d.z \
              + self.points[2]._local3d.z) / 3
