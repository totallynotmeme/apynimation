# /apynimation/animate.py
# has functions and handlers for animating values
# v0.0.0-indev  /  use current commit as the version


from . import Window, lerp


class Driver:
    def __init__(self, obj, prop, val=None):
        self.obj = obj
        self.prop = prop
        if val is None:
            # try to fetch default
            val = getattr(obj, prop, None)
        self.val = val

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.val} -> {self.obj}.{self.prop}>"

    def step(self, t=0):
        setattr(self.obj, self.prop, self.val)


class Towards(Driver):
    def __init__(self, *args, factor=None, **kwargs):
        # factor is PER FRAME. by default it uses Window.dt,
        # resulting in moving about ~63% towards goal per second
        super().__init__(*args, **kwargs)
        if factor is None:
            factor = Window.dt
        self.factor = factor
        self.goal = self.val # set by external script

    def _move(self):
        self.val = lerp(self.val, self.goal, self.factor)

    def step(self, t=0):
        self._move()
        super().step(t)


class TowardsLerp(Towards):
    # same as Towards, but uses a.lerp(b, f) instead of lerp(a, b, f).
    # this should be used for Vector's, Color's, or anything that supports .lerp

    def _move(self):
        self.val = self.val.lerp(self.goal, self.factor)
