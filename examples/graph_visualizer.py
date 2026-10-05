from apynimation import *
import random


# some info about controls
print("""
A funny graph visualizer thing
LMB - drag camera/node
shift + LMB - expand node (see Node.expand in code)
RMB while dragging - freeze node in place

mouse scroll - zoom in/out
TAB - expand 5 (or less) random nodes
R - reset graph back to initial state

[please note that this is just something i made in 3 hours as a fun demo project,
 it's not meant to be a final product or a usable app. there ARE bugs.           ]
""")


Window.set_res((1600, 900))
dt = Window.set_fps(60)
Window.create(caption="Graph")

half_window_res = pg.Vector2(Window.res) / 2


class Camera:
    pos = pg.Vector2()
    zoom = 1

    def project(point):
        return (point + Camera.pos) * Camera.zoom + half_window_res

    def unproject(point):
        return (point - half_window_res) / Camera.zoom - Camera.pos


font = pg.font.SysFont("consolas", 20)

class Node(Point):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val = None
        self.goal = pg.Vector2(self)
        self.projected = pg.Vector2(-999, -999)
        self.size = 50
        self.locked = False
        self.children = []
        self.expanded = False
        self.label = Text(font, align="center")

    def step(self, t=0):
        self.projected.update(Camera.project(self))
        # updating label pos (and text just in case)
        self.label.pos.update(self.projected)
        self.label.text = str(self.val)
        self.label.step(t)

        if self.children:
            self.size = sum(i.size for i in self.children) / 3 + 50
            angle_step = 360 / len(self.children)
            for ind, child in enumerate(self.children):
                dist = child.size * 3 + self.size
                up = pg.Vector2.from_polar((dist, angle_step * ind))
                child.goal.update(self + up)

        if not self.locked:
            self.update(self.lerp(self.goal, dt * 10))

    def draw(self, target):
        r = self.size * Camera.zoom
        pg.draw.circle(target, "white", self.projected, r, 1)
        if r > 10:
            self.label.draw(target)

        if self.locked:
            pg.draw.circle(target, "red", self.projected, r * 1.1, 1)

        for child in self.children:
            pg.draw.line(target, "white", self.projected, child.projected)

    def collidepoint(self, point):
        return self.projected.distance_to(point) <= self.size * Camera.zoom

    def fork(self, val):
        new = Node(self)
        new.val = val
        nodes.add(new)
        self.children.append(new)

    def expand(self):
        if self.expanded:
            return
        self.expanded = True

        # add your own splitting logic here
        for i in "0123456789":
            self.fork(self.val + i)

        self.size = len(self.children) * 5 + 50


nodes = Scene()
Window.scene = nodes

base_node = Node()
base_node.val = "."
nodes.add(base_node)


def scroll_handler(ev):
    Camera.zoom *= 1.1 ** ev.y
    Camera.zoom = min(max(Camera.zoom, 0.01), 2)

def key_handler(ev):
    if ev.key == pg.K_TAB:
        # random node expansion
        for i in range(5):
            random.choice(nodes.objects).expand()
    if ev.key == pg.K_r:
        # gotta be careful with the children to not cause a memory leak... in python
        for i in nodes.objects:
            i.children.clear()
        # then clear all other nodes
        nodes.objects.clear()
        nodes.add(base_node)
        # and some extra spaghetti to return to initial state
        base_node.expanded = False
        base_node.size = 50

Window.add_event_handler({
    pg.MOUSEWHEEL: scroll_handler,
    pg.KEYDOWN: key_handler,
})


dragging = None

while Window.is_open:
    # clicked on what?
    if Input.mouse_just_pressed[0]:
        dragging = None
        for i in nodes.objects:
            if i.collidepoint(Input.mouse_pos):
                dragging = i
                i.locked = False
                break

    # if shift clicked on a node, expand
    if Input.shift and dragging and Input.mouse_just_pressed[0]:
        dragging.expand()

    # dragging logic
    if Input.mouse_buttons[0]:
        if dragging is None:
            Camera.pos += Input.mouse_rel / Camera.zoom
        else:
            dragging.update(Camera.unproject(Input.mouse_pos))
            dragging.goal.update(dragging)
            if Input.mouse_buttons[2]:
                dragging.locked = True
                dragging = None

    Window.finish_frame()
