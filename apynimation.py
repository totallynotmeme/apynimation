import pygame as pg


DO_LITERALLY_NOTHING = lambda *a, **kwa: None


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

    def update():
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

    def set_fps(fps):
        Window.fps = fps
        Window.dt = 1/fps
        return Window.dt

    def finish_frame():
        # rendering
        Window.clear()
        if Window.scene is not None:
            Window.scene.render(Window.surface)
        for obj in Window.global_objects:
            obj.update(Window.t)
            obj.render(Window.surface)
        Window.post()

        pg.display.flip()
        Window.clock.tick(Window.fps)

        # handling stuff
        Window.t += Window.dt
        if Window.scene is not None:
            Window.scene.t += Window.dt

        Input.update()
        for ev in pg.event.get():
            Window.event_map.get(ev.type, DO_LITERALLY_NOTHING)(ev)

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

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.layers)} layers>"

    def render(self, target):
        for layer in self.layers:
            layer.render(target, t=self.t)

    def create_layer(self):
        a = Layer(self.size)
        self.layers.append(a)
        return a


# layers
class Layer:
    def __init__(self, size):
        self.objects = []
        self.surf = pg.Surface(size, pg.SRCALPHA)

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.objects)} objects>"

    def render(self, target, t=0):
        self.clear()

        for obj in self.objects:
            obj.update(t)
            obj.render(self.surf)

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
class Point:
    def __init__(self, x=0, y=0, data=None):
        self.pos = pg.Vector2(x, y)
        self.data = data or {}

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.pos}>"

    def update(self, t=0):
        pass

    def render(self, target):
        pixel_pos = (int(self.pos.x), int(self.pos.y))
        target.set_at(pixel_pos, "white")


class Point3d:
    # NOTE: this DOES NOT handle cases when the point is behind the camera
    # If the point is behind, it will end up being flipped back to the front

    def __init__(self, x=0, y=0, z=0, data=None):
        self.pos3d = pg.Vector3(x, y, z)
        self.pos = pg.Vector2()
        self.prev_t = -1
        self.data = data or {}

        self.update() # to set self.pos

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.pos3d}>"

    def update(self, t=0):
        # micro-optimization to prevent it from recomputing the same point 100 times
        if self.prev_t == t:
            return
        self.prev_t = t

        focal_len = self.data["focal_length"]
        pos3d = self.pos3d - self.data["camera_pos"]
        x = (pos3d.x * focal_len) / (pos3d.z + focal_len)
        y = (pos3d.y * focal_len) / (pos3d.z + focal_len)
        x += self.data["win_size"].x / 2
        y += self.data["win_size"].y / 2
        self.pos.update(x, y)

    def render(self, target):
        pixel_pos = (int(self.pos.x), int(self.pos.y))
        target.set_at(pixel_pos, "white")


# objects that are more useful than points
class Line:
    def __init__(self, p1, p2, color="white", width=1):
        self.p1 = p1
        self.p2 = p2
        self.width = width
        self.color = pg.Color(color)

    def __repr__(self):
        return f"<{self.__class__.__name__}  {self.p1} -- {self.p2}>"

    def update(self, t=0):
        self.p1.update(t)
        self.p2.update(t)

    def render(self, target):
        pg.draw.line(target, self.color, self.p1.pos, self.p2.pos, self.width)


class Wireframe:
    def __init__(self, points, color="white", width=1, closed=False):
        self.points = points
        self.color = pg.Color(color)
        self.width = width
        self.closed = closed

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.points)} points>"

    def update(self, t=0):
        for i in self.points:
            i.update(t)

    def render(self, target):
        positions = [i.pos for i in self.points]
        pg.draw.lines(target, self.color, self.closed, positions, self.width)


class Polygon:
    def __init__(self, points, color="white", width=0):
        self.points = points
        self.width = width
        self.color = pg.Color(color)

    def __repr__(self):
        return f"<{self.__class__.__name__} {len(self.points)} points>"

    def update(self, t=0):
        for i in self.points:
            i.update(t)

    def render(self, target):
        positions = [i.pos for i in self.points]
        pg.draw.polygon(target, self.color, positions, self.width)


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

    def update(self, t=0):
        if self.p2 is None:
            self.p1.update(t)
            self.x, self.y = self.p1.pos
        else:
            self.p1.update(t)
            self.p2.update(t)
            points = [self.p1.pos, self.p2.pos]
            left, right = sorted(i.x for i in points)
            top, bottom = sorted(i.y for i in points)
            self.x = left
            self.y = top
            self.w = right - left
            self.h = bottom - top # 0 is up, 100 is down
        self.rect.update(self.x, self.y, self.w, self.h)

    def render(self, target):
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
        self.update()

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.center} r={self.radius:.2f}px>"

    def update(self, t=0):
        self.center_point.update(t)
        self.center = self.center_point.pos
        if self.radius_point is not None:
            self.radius_point.update(t)
            self.radius = self.center.distance_to(self.radius_point.pos)

    def render(self, target):
        pg.draw.circle(target, self.color, self.center, self.radius, self.width)

    def collidepoint(self, point): # name based on pygame.Rect.collidepoint
        return self.center.distance_to(point) <= self.radius


class CircleNgon(Circle):
    def __init__(self, *args, sides=7, angle=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.sides = sides
        self.angle = angle

    def render(self, target):
        up = pg.Vector2(0, -self.radius)
        angle_step = 360 / self.sides
        points = []
        for i in range(self.sides):
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

    def update(self, t=0):
        if self.point is not None:
            self.point.update(t)
            self.pos.update(self.point.pos)

    def render(self, target):
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

    def update(self, t=0):
        super().update(t)
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
        if element not in self.elements:
            self.ind = -1
            return

        self.ind = self.elements.index(element)


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
    """

    def __init__(self, points):
        self.points = points
        self.update_points()

    def update_points(self):
        self.points.sort(key=lambda vec: vec.pos.x)

    def get(self, val):
        if val <= self.points[0].pos.x:
            return self.points[0].pos.y
        if val >= self.points[-1].pos.x:
            return self.points[-1].pos.y

        for prev_p, next_p in zip(self.points, self.points[1:]):
            if val < next_p.pos.x:
                dist = next_p.pos.x - prev_p.pos.x
                f = (val - prev_p.pos.x) / dist
                return next_p.pos.y * f + prev_p.pos.y * (1-f)
