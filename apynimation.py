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
    def __init__(self, x=0, y=0, data=None):
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
    
    def __init__(self, x=0, y=0, z=0, data=None):
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


# ...more category separations?
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


# circles
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
