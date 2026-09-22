# /apynimation/logic.py
# has most classes that simplify handling the scene logic
# v0.0.0-indev  /  use current commit as the version

from . import Window


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
