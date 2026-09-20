import pygame as pg
from math import ceil


# helper functions / aliases to existing functions for easier access
# ceil - imported above
lerp = pg.math.lerp


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


# setting up the window
class Window:
    # no __init__ because pygame doesn't support multiple windows, and
    # i don't see a point in implementing virtual windows or something
    is_open = False
    surface = None
    clock = None

    scene = None
    global_objects = []
    event_map = {}

    fps = 60 # default
    dt = 1/60
    t = 0

    def create(size, caption="Untitled window", **kwargs):
        # surely nothing will break if you try to call create() multiple times
        pg.init()
        pg.display.set_caption(caption)
        Window.surface = pg.display.set_mode(size, **kwargs)
        Window.clock = pg.time.Clock()
        Window.is_open = True

    def close(ev=None): # ev argument used for event handling
        Window.is_open = False
        pg.quit()
        return True

    def set_fps(fps):
        Window.fps = fps
        Window.dt = 1/fps
        return Window.dt

    def finish_frame():
        # rendering
        Window.clear()
        if Window.scene is not None:
            Window.scene.draw(Window.surface)
        for obj in Window.global_objects:
            obj.step(Window.t)
            obj.draw(Window.surface)
        Window.post()

        pg.display.flip()
        Window.clock.tick(Window.fps)

        # handling stuff
        Window.t += Window.dt
        if Window.scene is not None:
            Window.scene.t += Window.dt

        Input.step()
        for ev in pg.event.get():
            func = Window.event_map.get(ev.type)
            if func is not None:
                if func(ev):
                    # event handled by Window, don't pass through to scene
                    continue

            # pass event to Scene if it's set
            if Window.scene is None:
                continue
            func = Window.scene.event_map.get(ev.type)
            if func is not None:
                func(ev)

    def add_event_handler(new_map, _nowarn=False):
        Window.event_map.update(new_map)
        if pg.QUIT in new_map and not _nowarn:
            msg = """
[WARN] QUIT event has been overwritten, which might result in an unclosable window.
If you're writing your own handler, make sure to call Window.close() when you're done.
Add _nowarn=True parameter to remove this warning
"""[1:-1]
            print(msg)

    # utility functions that can be overwritten to create special effects
    def clear(): # runs before the frame is drawn
        Window.surface.fill("black")

    def post(): # runs after the frame is drawn, unused by default
        pass

Window.event_map[pg.QUIT] = Window.close # default


# scene stuff
class Scene:
    def __init__(self, size):
        self.t = 0
        self.size = size
        self.layers = []
        self.event_map = {}

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.layers)} layers>"

    def draw(self, target):
        for layer in self.layers:
            layer.draw(target, t=self.t)

    def create_layer(self):
        a = Layer(self.size)
        self.layers.append(a)
        return a

    def add_event_handler(self, new_map, _nowarn=False):
        # _nowarn to keep parity between Window and Scene, unused here
        self.event_map.update(new_map)


# layers
class Layer:
    def __init__(self, size):
        self.objects = []
        self.surf = pg.Surface(size, pg.SRCALPHA)

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.objects)} objects>"

    def draw(self, target, t=0):
        self.clear()

        for obj in self.objects:
            obj.step(t)
            obj.draw(self.surf)

        self.blit(target)

    def add(self, *objects):
        self.objects.extend(objects)
        if len(objects) == 1:
            return objects[0]
        return objects

    # utility functions that can be overwritten to create layer-specific effects
    def clear(self):
        self.surf.fill((0, 0, 0, 0))

    def blit(self, target):
        target.blit(self.surf, (0, 0))


# points
class Point(pg.Vector2):
    # Vector2's __init__ works here, no need to re-define it

    def __repr__(self):
        return f"<{self.__class__.__name__} @ ({self.x}, {self.y})>"

    def step(self, t=0):
        # overwrite this function to automatically update the point based on time
        pass

    def draw(self, target):
        pixel_pos = (int(self.x), int(self.y))
        target.set_at(pixel_pos, "white")


class Point3d(Point):
    # NOTE: this DOES NOT handle cases when the point is behind the camera
    # If the point is behind, it will end up being flipped back to the front

    def __init__(self, x=0, y=0, z=0, data=None):
        self.pos3d = pg.Vector3(x, y, z)
        self.data = data or {}
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

        focal_len = self.data["focal_length"]
        pos3d = self.pos3d - self.data["camera_pos"]
        # TODO: make it work properly for z<0, or fallback to an unset value?
        # or even move this out to apynimation_3d submodule/addon/thing???
        if pos3d.z + focal_len <= 0:
            self.valid = False
            return

        self.x = (pos3d.x * focal_len) / (pos3d.z + focal_len)
        self.y = (pos3d.y * focal_len) / (pos3d.z + focal_len)
        self.x += self.data["win_size"].x / 2
        self.y += self.data["win_size"].y / 2
        self.valid = True


# objects that are more useful than points
class Line:
    def __init__(self, p1, p2, color="white", width=1):
        self.p1 = p1
        self.p2 = p2
        self.width = width
        self.color = pg.Color(color)

    def __repr__(self):
        return f"<{self.__class__.__name__}  {self.p1} -- {self.p2}>"

    def step(self, t=0):
        if isinstance(self.p1, Point):
            self.p1.step(t)
        if isinstance(self.p2, Point):
            self.p2.step(t)

    def draw(self, target):
        pg.draw.line(target, self.color, self.p1, self.p2, self.width)


class Polygon:
    def __init__(self, points, color="white", width=0):
        self.points = points
        self.color = pg.Color(color)
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
class Rect:
    def __init__(self, p1, p2=None, w=50, h=20, color="white", width=0):
        self.p1 = p1
        self.p2 = p2
        self.w = w
        self.h = h
        self.color = color
        self.width = width # bruh
        self.rect = pg.Rect(0, 0, 0, 0)

    def __repr__(self):
        if self.p2 is None:
            suffix = f"{self.w}x{self.h}"
        else:
            suffix = f"-- {self.p2}"
        return f"{self.__class__.__name__}  {self.p1} {suffix}"

    def step(self, t=0):
        if self.p2 is None:
            if isinstance(self.p1, Point):
                self.p1.step(t)
            self.x, self.y = self.p1
        else:
            if isinstance(self.p1, Point):
                self.p1.step(t)
            if isinstance(self.p2, Point):
                self.p2.step(t)
            points = [self.p1, self.p2]
            left, right = sorted(i.x for i in points)
            top, bottom = sorted(i.y for i in points)
            self.x = left
            self.y = top
            self.w = right - left
            self.h = bottom - top # 0 is up, 100 is down
        self.rect.update(self.x, self.y, self.w, self.h)

    def draw(self, target):
        pg.draw.rect(target, self.color, self.rect, self.width)

    def collidepoint(self, point):
        return self.rect.collidepoint(point)


class Circle:
    def __init__(self, center_point, radius_point=None, color="white", width=1, radius=0):
        self.center_point = center_point
        self.radius_point = radius_point
        self.center = pg.Vector2()
        self.radius = radius # gets automatically set if radius_point is a Point()
        self.width = width
        self.color = pg.Color(color)
        self.step()

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.center} r={self.radius:.2f}px>"

    def step(self, t=0):
        if isinstance(self.center_point, Point):
            self.center_point.step(t)
        self.center.update(self.center_point)
        if self.radius_point is not None:
            if isinstance(self.radius_point, Point):
                self.radius_point.step(t)
            self.radius = self.center.distance_to(self.radius_point)

    def draw(self, target):
        pg.draw.circle(target, self.color, self.center, self.radius, self.width)

    def collidepoint(self, point): # name based on pygame.Rect.collidepoint
        return self.center.distance_to(point) <= self.radius


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
class Sprite: # (pg.sprite.Sprite)
    def __init__(self, pos=(0, 0), point=None, surface=None, align="topleft"):
        self.pos = pg.Vector2(pos)
        self.point = point
        self.surface = surface
        self.align = align
        self.rect = pg.Rect(0, 0, 0, 0)

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.pos}>"

    def step(self, t=0):
        if self.point is not None:
            if isinstance(self.point, Point):
                self.point.step(t)
            self.pos.update(self.point)

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


# utility classes that simplify handling the scene logic
class Ticker:
    def __init__(self, time, wrap=False, _val=0):
        self.time = time
        self.wrap = wrap
        self._val = _val

    def __repr__(self):
        return f"Ticker(time={self.time} wrap={self.wrap} _val={self._val})"

    def step(self, dt=None):
        self._val += dt or Window.dt

        if self._val < self.time:
            return False # not yet

        if self.wrap:
            self._val -= self.time
        else: # reset the whole thing
            self._val = 0
        return True


class Tape:
    """
    [[placeholder docstring]]
    an infinite 'tape' of looping values that can be cycled through.

    example usage:
    a = Tape([1, 2, 3])
    for _ in range(6):
        print(a.next(), end="; ") # 1; 2; 3; 1; 2; 3;
    print()
    for _ in range(5):
        print(a.prev(), end="; ") # 2; 1; 3; 2; 1;
    print()

    NOTE: this can be imitated with itertools.cycle() using:
    a = itertools.cycle([1, 2, 3])
    for _ in range(6):
        print(next(a), end="; ") # 1; 2; 3; 1; 2; 3;
    print()
    # .prev() function cannot be recreated this way as far as i know
    """

    def __init__(self, elements=None, _ind=-1):
        self.elements = elements or []
        self.ind = _ind

    def __repr__(self):
        return f"<Tape x{len(self.elements)} elements ind={self.ind}>"

    # these two can probably be merged into a generic .shift()
    # but i find .prev() and .next() more readable
    def prev(self, n=1):
        if not self.elements:
            return None

        if self.ind == -1:
            self.ind = len(self.elements) - 1
        else:
            self.ind -= n
            self.ind %= len(self.elements)

        return self.elements[self.ind]

    def next(self, n=1):
        if not self.elements:
            return None

        if self.ind == -1:
            self.ind = 0
        else:
            self.ind += n
            self.ind %= len(self.elements)

        return self.elements[self.ind]

    def set(self, element):
        if element in self.elements:
            self.ind = self.elements.index(element)
        else:
            self.ind = -1


class Limiter:
    """
    [[placeholder docstring]]
    a helper class to ratelimit events

    example usage:
    a = Limiter(0.5) # time in seconds
    def callback(ev):
        if a.call() and ev.button == pg.BUTTON_LEFT:
            print("you just left clicked! you can left click again in 0.5s")
    Window.add_event_handler({pg.MOUSEBUTTONDOWN: callback})
    """

    def __init__(self, cooldown, _last_call=None):
        self.cooldown = cooldown
        self.last_call = _last_call or -999999999 # float("-inf") doesn't exist

    def __repr__(self):
        return f"<Limiter every {self.cooldown}s>"

    def call(self):
        dt = Window.t - self.last_call

        if 0 <= dt < self.cooldown:
            return False

        self.last_call = Window.t
        return True


class Curve:
    """
    [[placeholder docstring]]
    a helper class for animating values using a "piecewise linear function"
    (aka points connected with straight lines)
    a curve must have at least 1 point, although it's only useful with 2 or more

    example usage:
    a = Curve([
        Point(0, 100),
        Point(1, 250),
        Point(2, 250),
        Point(3, 100),
    ])
    circle = Circle(...)
    # inside the window loop
    while Window.is_open:
        circle.radius = a.get(Window.t % 4)
        Window.finish_frame()
    # this will animate the circle radius as:
    # 0-1s - growing from 100px to 250px
    # 1-2s - staying at 250px
    # 2-3s - shrinking from 250px to 100px
    # 3-4s - staying at 100px
    """

    def __init__(self, points):
        self.points = points
        self.update_points()

    def update_points(self):
        self.points.sort(key=lambda vec: vec.x)

    def get(self, val):
        if val <= self.points[0].x:
            return self.points[0].y
        if val >= self.points[-1].x:
            return self.points[-1].y

        for prev_p, next_p in zip(self.points, self.points[1:]):
            if val < next_p.x:
                dist = next_p.x - prev_p.x
                f = (val - prev_p.x) / dist
                return next_p.y * f + prev_p.y * (1-f)


class Timer:
    """
    [[placeholder docstring]]
    a class for making something happen after a certain amount of time

    example usage:
    a = Timer(3)
    a.start()
    while Window.is_open:
        if a.step():
            print("The timer has finished!")
        Window.finish_frame()
    """

    def __init__(self, time):
        self.time = time
        self.trigger_at = -1

    def __repr__(self):
        return f"<Timer {self.time}s>"

    def start(self, restart=False):
        if not restart and self.trigger_at >= 0:
            return False

        self.trigger_at = Window.t + self.time
        return True

    def step(self):
        if self.trigger_at < 0:
            return False

        if Window.t >= self.trigger_at:
            self.trigger_at = -1
            return True
        return False


class Trail:
    """
    [[placeholder docstring]]
    a class for listing the last few objects put. most useful for drawing trails

    NOTE: when used to store points, it's recommended to use point.copy(),
    otherwise the trail might not work properly.

    example usage:
    trail = Trail(100)
    # draw lines between the points
    scene_layer.add(Wireframe(trail.items))
    while Window.is_open:
        # use current mouse position as the new point
        trail.put(Input.mouse_pos.copy())
        Window.finish_frame()
    """

    def __init__(self, size):
        self.items = []
        self.size = size

    def __repr__(self):
        return f"<Trail {len(self.items)}/{self.size} items>"

    def put(self, value):
        if len(self.items) < self.size:
            self.items.insert(0, value)
        else:
            # [0, 1, 2] -> [new, 0, 1] and throw away 2
            self.items[1:] = self.items[:-1]
            self.items[0] = value

    def clear(self):
        self.items.clear()
