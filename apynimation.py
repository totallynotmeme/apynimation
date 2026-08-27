import pygame as pg


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
    
    def add(self, obj):
        self.objects.append(obj)
        return obj
    
    # utility functions that can be overwritten to create layer-specific effects
    def clear(self):
        self.surf.fill((0, 0, 0, 0))
    
    def blit(self, target):
        target.blit(self.surf, (0, 0))


# objects
class Point:
    def __init__(self, x, y, data=None):
        self.pos = pg.Vector2(x, y)
        if data is None:
            data = {}
        self.data = data
    
    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.pos}>"
    
    def update(self, t=0):
        pass
    
    def render(self, target):
        pixel_pos = (int(self.pos.x), int(self.pos.y))
        target.set_at(pixel_pos, "white")


class Point3d:
    # NOTE: this DOES NOT handle cases when the point is behind the camera.
    # If the point is behind, it will end up being flipped back to the front.
    
    def __init__(self, x, y, z, data=None):
        self.pos3d = pg.Vector3(x, y, z)
        self.pos = pg.Vector2()
        self.prev_t = -1
        if data is None:
            data = {}
        self.data = data
        
        self.update() # to set self.pos
    
    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.pos3d}>"
    
    def update(self, t=0):
        # micro-optimization to prevent it from recomputing the same point 100 times
        if self.prev_t == t:
            return
        self.prev_t = t
        
        fov = self.data["focal_length"]
        pos3d = self.pos3d - self.data["camera_pos"]
        x = (pos3d.x * fov) / (pos3d.z + fov)
        y = (pos3d.y * fov) / (pos3d.z + fov)
        x += self.data["win_size"].x / 2
        y += self.data["win_size"].y / 2
        self.pos.update(x, y)
    
    def render(self, target):
        pixel_pos = (int(self.pos.x), int(self.pos.y))
        target.set_at(pixel_pos, "white")


# ...more category separations?
class Line:
    def __init__(self, p1, p2, color="white"):
        self.p1 = p1
        self.p2 = p2
        self.color = pg.Color(color)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}  {self.p1} -- {self.p2}>"
    
    def update(self, t=0):
        self.p1.update(t)
        self.p2.update(t)
    
    def render(self, target, offset=(0, 0)):
        pg.draw.line(target, self.color, self.p1.pos, self.p2.pos)


class Segment:
    def __init__(self, points, color="white"):
        self.points = points
        self.color = pg.Color(color)
        self.closed = False
    
    def __repr__(self):
        return f"<{self.__class__.__name__}  {len(self.points)} points>"
    
    def update(self, t=0):
        for i in self.points:
            i.update(t)
    
    def render(self, target, offset=(0, 0)):
        positions = [i.pos for i in self.points]
        pg.draw.lines(target, self.color, self.closed, positions)
