# /apynimation/animate.py
# has functions and handlers for animating values
# v0.0.0-indev  /  use current commit as the version


from . import Window, lerp, clamp


class Animator:
    active = True

    def __init__(self, _hooked=None):
        if _hooked is not None:
            self.hooked = _hooked
            return
        self.hooked = [] # (obj, prop, driver),

    def step(self, t=0):
        for obj, prop, driver in self.hooked:
            val = getattr(obj, prop)
            if val != driver.val:
                # value was changed, update the goal
                driver.prev = driver.val
                driver.goal = val
                driver.last_t = t
            anim_t = t - driver.last_t
            driver.step(anim_t)
            setattr(obj, prop, driver.val)

    def hook(self, obj, prop, driver, *args, **kwargs):
        a = driver(*args, **kwargs)
        self.hooked.append((obj, prop, a))
        # set default
        val = getattr(obj, prop)
        a.prev = val
        a.goal = val
        a.val = val


class Driver:
    def __init__(self):
        self.prev = 0
        self.goal = 0
        self.val = 0
        self.last_t = 0

    def __repr__(self):
        return f"<{self.__class__.__name__}  {self.prev} -> {self.goal} (={self.val})>"

    def step(self, anim_t):
        return NotImplemented


class Towards(Driver):
    def __init__(self, speed=5):
        # factor is PER FRAME. by default it uses Window.dt,
        # resulting in moving about ~63% towards goal per second
        super().__init__()
        self.speed = speed

    def step(self, anim_t):
        self.val = lerp(self.val, self.goal, self.speed * Window.dt)


class TowardsLerp(Towards):
    # same as Towards, but uses a.lerp(b, f) instead of lerp(a, b, f).
    # this should be used for Vector's, Color's, or anything that supports .lerp

    def step(self, anim_t):
        self.val = self.val.lerp(self.goal, self.speed * Window.dt)


class Linear(Driver):
    def __init__(self, time=1):
        # time in seconds to reach the goal
        super().__init__()
        self.time = time

    def step(self, anim_t):
        t = clamp(anim_t / self.time, 0, 1)
        self.val = lerp(self.prev, self.goal, t)
