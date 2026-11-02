# /apynimation/__init__.py
# contains basic objects and classes for creating a functional window
# v0.0.0-indev  /  use current commit as the version

import pygame as pg
import pygame.locals
from math import ceil


# helper functions / aliases to existing functions for easier access
# ceil - imported above
lerp = pg.math.lerp

# for @event_handler decorators
def _guess_event_type(name):
    func_name = name.upper().replace("_", "")
    func_name = func_name.removeprefix("ON").removesuffix("HANDLER")
    ev_type = getattr(pg.locals, func_name, None)
    if ev_type is None:
        # oops
        raise ValueError(f"""
Failed to guess event handler type. Please specify the event type with \
'def on_EVENT_TYPE(...)', 'def EVENT_TYPE_handler(...)', or at decorator with \
'@event_handler(pg.EVENT_TYPE)'
"""[1:-1])
    return ev_type



# user inputs
class Input:
    mouse_pos = pg.Vector2()
    mouse_prev_pos = pg.Vector2()
    mouse_rel = pg.Vector2()
    mouse_buttons = [False] * 3
    mouse_just_pressed = [False] * 3
    mouse_just_released = [False] * 3

    keyboard_keys = None
    shift = False
    ctrl = False
    alt = False

    def step():
        Input.mouse_prev_pos.update(Input.mouse_pos)
        Input.mouse_pos.update(pg.mouse.get_pos())
        Input.mouse_rel.update(Input.mouse_pos - Input.mouse_prev_pos)

        new_buttons = pg.mouse.get_pressed()
        Input.mouse_just_pressed = [
            new_buttons[0] and not Input.mouse_buttons[0],
            new_buttons[1] and not Input.mouse_buttons[1],
            new_buttons[2] and not Input.mouse_buttons[2],
        ]
        Input.mouse_just_released = [
            not new_buttons[0] and Input.mouse_buttons[0],
            not new_buttons[1] and Input.mouse_buttons[1],
            not new_buttons[2] and Input.mouse_buttons[2],
        ]
        Input.mouse_buttons = new_buttons

        Input.keyboard_keys = pg.key.get_pressed()
        mods = pg.key.get_mods()
        Input.shift = bool(mods & pg.KMOD_SHIFT)
        Input.ctrl = bool(mods & pg.KMOD_CTRL)
        Input.alt = bool(mods & pg.KMOD_ALT)


# some base classes
class Container:
    active = True # default

    # object capable of containing steppable and drawable objects
    def __init__(self):
        self.objects = []

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.objects)} objects>"

    def step(self, t=0):
        for obj in self.objects:
            if obj.active:
                obj.step(t)

    def draw(self, target):
        for obj in self.objects:
            if obj.active:
                obj.draw(target)

    def add(self, *objects):
        self.objects.extend(objects)
        if len(objects) == 1:
            return objects[0]
        return objects

    def remove(self, *objects):
        for obj in objects:
            if obj in self.objects:
                self.objects.remove(obj)


class Drawable:
    active = True # default

    def step(self, t=0):
        return NotImplemented

    def draw(self, target):
        return NotImplemented


# if there's a window in Windows, is there a linu in Linux?
class _WindowClass(Container):
    def __init__(self):
        # this should not be used to create multiple Window objects,
        # but you do you.
        super().__init__()

        self.is_open = False
        self.surface = None
        self.clock = None

        self.scene = None
        self.event_map = {}

        self.res = (640, 480) # default
        self.center = pg.Vector2(self.res) / 2
        self.fps = 60 # default
        self.dt = 1/60
        self.t = 0

    def create(self, caption="Untitled window", **kwargs):
        # surely nothing will break if you try to call create() multiple times
        pg.init()
        pg.display.set_caption(caption)
        self.surface = pg.display.set_mode(self.res, **kwargs)
        self.clock = pg.time.Clock()
        self.is_open = True
        Input.step()
        # double-check the window size in case system changes it (ex: pydroid)
        self.set_res(self.surface.get_size())

    def close(self, ev=None): # ev argument used for event handling
        self.is_open = False
        pg.quit()
        return True

    def set_fps(self, fps):
        self.fps = fps
        self.dt = 1/fps
        return self.dt

    def set_res(self, res):
        self.res = res
        self.center = pg.Vector2(res) / 2
        return self.center

    def finish_frame(self):
        scene = self.scene
        # rendering
        self.clear()
        if scene is not None:
            scene.step_and_draw(self.surface)

        for obj in self.objects:
            if obj.active:
                obj.step(self.t)
                obj.draw(self.surface)

        self.post()
        pg.display.flip()
        self.clock.tick(self.fps)

        # handling stuff
        self.t += self.dt
        if scene is not None:
            scene.t += self.dt

        Input.step()
        for ev in pg.event.get():
            func = self.event_map.get(ev.type)
            if func is not None:
                if func(ev):
                    # event handled by Window, don't pass through to scene
                    continue

            # pass event to Scene if it's set
            if scene is None:
                continue
            func = scene.event_map.get(ev.type, scene.global_handler)
            if func is not None:
                func(ev)

    def event_handler(self, arg, _nowarn=False):
        # a decorator-ish way to define an event handler
        if type(arg) is int:
            # @event_handler(pg.EVENT_TYPE) / def func(...)
            ev_type = arg
            def _adder(func):
                self.add_event_handler({ev_type: func}, _nowarn=_nowarn)
                return func
            return _adder
        # assuming @event_handler / def on_EVENT_TYPE(...)
        func = arg
        ev_type = _guess_event_type(func.__name__)
        # hopefully it's a valid event
        name = pg.event.event_name(ev_type)
        #print(f"@event_handler: guessed {func.__name__} to be {name} ({ev_type})")
        self.add_event_handler({ev_type: func}, _nowarn=_nowarn)
        return func

    def add_event_handler(self, new_map, _nowarn=False):
        self.event_map.update(new_map)
        if pg.QUIT in new_map and not _nowarn:
            msg = """
[WARN] QUIT event has been overwritten, which might result in an unclosable window.
If you're writing your own handler, make sure to call Window.close() when you're done.
Add _nowarn=True parameter to remove this warning
"""[1:-1]
            print(msg)

    # utility functions that can be overwritten to create special effects
    def clear(self): # runs before the frame is drawn
        self.surface.fill("black")

    def post(self): # runs after the frame is drawn, unused by default
        pass

Window = _WindowClass()
Window.event_map[pg.QUIT] = Window.close # default


# actually usable containers
class Scene(Container):
    global_handler = None # default

    def __init__(self):
        self.t = 0
        self.layers = []
        self.objects = []
        self.event_map = {}

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.layers)} layers>"

    def step_and_draw(self, target):
        for layer in self.layers:
            if layer.active:
                layer.step(self.t)
                layer.draw(target)

        if self.objects:
            super().step(self.t)
            super().draw(target)

    def create_layer(self, *args, **kwargs):
        a = Layer(*args, **kwargs)
        self.layers.append(a)
        return a

    def event_handler(self, arg, _nowarn=False):
        # mirror of Window.event_handler decorator
        if type(arg) is int:
            # @event_handler(pg.EVENT_TYPE) / def func(...)
            ev_type = arg
            def _adder(func):
                self.event_map[ev_type] = func
                return func
            return _adder
        # assuming @event_handler / def on_EVENT_TYPE(...)
        func = arg
        ev_type = _guess_event_type(func.__name__)
        name = pg.event.event_name(ev_type)
        #print(f"@event_handler: guessed {func.__name__} to be {name} ({ev_type})")
        self.event_map[ev_type] = func
        return func

    def add_event_handler(self, new_map, _nowarn=False):
        # _nowarn to keep parity between Window and Scene, unused here
        self.event_map.update(new_map)


# layers
class Layer(Container):
    DISABLE_BUFFER = False

    def __init__(self, _surface_flags=pg.SRCALPHA):
        self.objects = []
        self.surf = pg.Surface(Window.res, _surface_flags)

    def draw(self, target):
        if self.DISABLE_BUFFER:
            # removes the overhead of blitting a buffer surface,
            # but doesn't allow pre- and post-effects
            if self.objects:
                super().draw(target)
            return

        self.clear()

        if self.objects:
            super().draw(self.surf)

        self.blit(target)

    # utility functions that can be overwritten to create layer-specific effects
    def clear(self):
        self.surf.fill((0, 0, 0, 0))

    def blit(self, target):
        target.blit(self.surf, (0, 0))


# points
class Point(pg.Vector2): # technically also Drawable
    # Vector2's __init__ works here, no need to re-define it
    active = True

    def __repr__(self):
        return f"<{self.__class__.__name__} @ ({self.x}, {self.y})>"

    def step(self, t=0):
        # overwrite this function to automatically update the point based on time
        pass

    def draw(self, target):
        pixel_pos = (int(self.x), int(self.y))
        target.set_at(pixel_pos, "white")


class OffsetPoint(Point):
    def __init__(self, anchor, offset=None):
        super().__init__()
        self.anchor = anchor
        self.offset = offset
        self.step()

    def step(self, t=0):
        self.update(self.anchor)
        self += self.offset


# objects that are more useful than points
class Line(Drawable):
    def __init__(self, p1, p2, color="white", width=1):
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.width = width

    def __repr__(self):
        return f"<{self.__class__.__name__}  {self.p1} -- {self.p2}>"

    def step(self, t=0):
        if isinstance(self.p1, Point):
            self.p1.step(t)
        if isinstance(self.p2, Point):
            self.p2.step(t)

    def draw(self, target):
        pg.draw.line(target, self.color, self.p1, self.p2, self.width)


class Polygon(Drawable):
    def __init__(self, points, color="white", width=0):
        self.points = points
        self.color = color
        self.width = width

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.points)} points>"

    def step(self, t=0):
        for i in self.points:
            if isinstance(i, Point):
                i.step(t)

    def draw(self, target):
        if len(self.points) < 2:
            return
        pg.draw.polygon(target, self.color, self.points, self.width)


class Wireframe(Polygon):
    def __init__(self, points, color="white", width=1, closed=False):
        super().__init__(points, color=color, width=width)
        self.closed = closed

    def draw(self, target):
        if len(self.points) < 2:
            return
        pg.draw.lines(target, self.color, self.closed, self.points, self.width)


# shapes
class Rect(Drawable):
    def __init__(self, x=0, y=0, w=50, h=20, color="white", width=0, p1=None, p2=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.width = width # bruh
        self.rect = pg.Rect(0, 0, 0, 0)
        # if self.p1 is None and self.p2 is not None:
        #     raise something i guess??

    def __repr__(self):
        return f"<{self.__class__.__name__} ({self.x}, {self.y}) {self.w}x{self.h}>"

    def step(self, t=0):
        if isinstance(self.p1, Point):
            self.p1.step()
        if isinstance(self.p2, Point):
            self.p2.step()

        if self.p1 is None:
            # no points set (p1=None p2=Point() is invalid)
            pass
        elif self.p2 is None:
            # only p1 (topleft) is set
            self.x, self.y = self.p1
        else:
            # both p1 and p2 are set
            self.x = min(self.p1[0], self.p2[0])
            self.y = min(self.p1[1], self.p2[1])
            self.w = abs(self.p1[0] - self.p2[0])
            self.h = abs(self.p1[1] - self.p2[1])
        self.rect.update(self.x, self.y, self.w, self.h)

    def draw(self, target):
        pg.draw.rect(target, self.color, self.rect, self.width)

    def collidepoint(self, point):
        return self.rect.collidepoint(point)


class Circle(Drawable):
    def __init__(self, center, r=20, color="white", width=1):
        self.center = center
        self.radius = r
        self.color = color
        self.width = width

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.center} r={self.radius:.2f}px>"

    def step(self, t=0):
        if isinstance(self.center, Point):
            self.center.step(t)

    def draw(self, target):
        pg.draw.circle(target, self.color, self.center, self.radius, self.width)

    def collidepoint(self, point): # name based on pygame.Rect.collidepoint
        return self.center.distance_to(point) <= self.radius


class CircleAnchored(Circle):
    def __init__(self, center, anchor, *args, **kwargs):
        super().__init__(center, *args, **kwargs)
        self.anchor = anchor
        self.step()

    def step(self, t=0):
        super().step(t)
        if isinstance(self.anchor, Point):
            self.anchor.step(t)
        self.radius = self.center.distance_to(self.anchor)


class CircleNgon(Circle):
    def __init__(self, *args, sides=7, angle=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.sides = sides
        self.angle = angle

    def draw(self, target):
        up = pg.Vector2(0, -self.radius)
        angle_step = 360 / self.sides
        points = []
        for i in range(ceil(self.sides)):
            points.append(self.center + up.rotate(i * angle_step + self.angle))
        pg.draw.polygon(target, self.color, points, self.width)


# something other than vector graphics
class Sprite(Drawable):
    def __init__(self, surface, pos=None, align="topleft"):
        self.surface = surface
        self.pos = pos or pg.Vector2()
        self.align = align
        self.rect = pg.Rect(0, 0, 0, 0)

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.pos}>"

    def step(self, t=0):
        if isinstance(self.pos, Point):
            self.pos.step(t)

    def draw(self, target):
        pos = self.surface.get_rect(**{self.align: self.pos})
        new_rect = target.blit(self.surface, pos)
        self.rect.update(new_rect)

    def collidepoint(self, point):
        return self.rect.collidepoint(point)


pg.font.init() # required for fonts to work
class Text(Sprite):
    def __init__(self, font, text="[...]", color="white", **kwargs):
        surface = font.render(text, True, color)
        super().__init__(surface=surface, **kwargs)

        self.text = text
        self.font = font
        self.color = color
        self._prev_render = (self.font, self.text, self.color)

    def step(self, t=0):
        super().step(t)
        this_render = (self.font, self.text, self.color)
        if self._prev_render != this_render:
            self._prev_render = this_render
            self.surface = self.font.render(self.text, True, self.color)
