from apynimation import *
from apynimation import logic

win_size = (1600, 900)
fps = 60


class Viewport:
    w = win_size[1] - 50
    h = win_size[1] - 50
    x_from = 0
    x_to = 1
    y_from = 0
    y_to = 1

    editing_what = None
    editing_text = ""

    def keep_in_view(point):
        if point.x < 0:
            point.x = 0
        elif point.x > Viewport.w:
            point.x = Viewport.w
        if point.y < 0:
            point.y = 0
        elif point.y > Viewport.h:
            point.y = Viewport.h

    def set_value(name, val):
        if name == "x_from":
            Viewport.x_from = val
        if name == "y_from":
            Viewport.y_from = val
        if name == "x_to":
            Viewport.x_to = val
        if name == "y_to":
            Viewport.y_to = val

        if Viewport.x_to <= Viewport.x_from:
            Viewport.x_to = Viewport.x_from + 0.01
        if Viewport.y_to <= Viewport.y_from:
            Viewport.y_to = Viewport.y_from + 0.01

    def collidepoint(point):
        if point.x < 0 or point.y < 0:
            return False
        if point.x > Viewport.w or point.y > Viewport.h:
            return False
        return True


curve_points = {
    0: 0,
    0.5: 0.72,
    1: 1,
}

class CurvePoint(Point):
    dragging = None

    def __init__(self, where, val):
        super().__init__()
        self.where = where
        self.val = val
        self.pulse_t = 999
        self.dragging = False
        self.x = self.where * Viewport.w
        self.y = (1-self.val) * Viewport.h

    def step(self, t=0):
        self.pulse_t += 50 * dt
        if CurvePoint.dragging == self:
            # drag the point
            self.update(Input.mouse_pos)
            Viewport.keep_in_view(self)
            self.where = self.x / Viewport.w
            self.val = 1 - self.y / Viewport.h

    def draw(self, target):
        pg.draw.circle(target, "white", self, 20, 1)
        pg.draw.circle(target, "white", self, 5)
        # pulse on release
        if self.pulse_t < 50/3:
            radius = 15 * self.pulse_t ** 0.5
            width = int(50/3 - self.pulse_t + 1)
            pg.draw.circle(target, "white", self, radius, width)

    def collidepoint(self, point):
        return self.distance_to(point) < 20

    def bake_point(self):
        curve_points[self.where] = self.val


main = Scene()

preview_point = Point()
preview_circle = main.add(Circle(preview_point, color="red", radius=7, width=0))

visual_points = []
for key, val in curve_points.items():
    a = CurvePoint(key, val)
    main.add(a)
    visual_points.append(a)

curve = logic.Curve(curve_points)


def refresh_points():
    curve_points.clear()
    for i in visual_points:
        i.bake_point()
    curve.update_points()
    wireframe.points.sort(key=lambda point: point.x)


wireframe = Wireframe(visual_points)
main.add(wireframe)

edge_l = Line(Point(), Point())
edge_r = Line(Point(), Point())
main.add(edge_l, edge_r)

trail = Sprite((0, win_size[1] - 20))
trail.surface = pg.Surface((win_size[0], 20))
main.add(trail)

left_edge = Point(0, win_size[1]-25) # x gets set later in the code
right_edge = Point(win_size[0], win_size[1]-25)
unit_length = Line(left_edge, right_edge, width=3)
main.add(unit_length)


font = pg.font.SysFont("consolas", 25)
label_x_from = Text(font, pos=(Viewport.w+30, 15))
label_x_to = Text(font, pos=(Viewport.w+350, 15))
label_y_from = Text(font, pos=(Viewport.w+30, 45))
label_y_to = Text(font, pos=(Viewport.w+350, 45))
labels = main.add(label_x_from, label_x_to, label_y_from, label_y_to)

label_x_from._value = "x_from"
label_y_from._value = "y_from"
label_x_to._value = "x_to"
label_y_to._value = "y_to"


export_button = Rect(Point(Viewport.w + 30, 120), w=250, h=60)
export_button.step() # setting up .rect.center
button_origin = export_button.rect.center

font = pg.font.SysFont("consolas", 20)
export_label = Text(font, "Export curve points", pos=button_origin, align="center")
main.add(export_button, export_label)


def click_handler(ev):
    if ev.button == pg.BUTTON_LEFT:
        # handling text labels
        if Viewport.editing_what:
            # cancel editing (simulate fake keyboard press)
            keyboard_handler("_RETURN")
        for i in labels:
            if i.collidepoint(Input.mouse_pos):
                Viewport.editing_what = i
                Viewport.editing_text = ""
                i.color = "yellow"
        # messing with the graph
        for i in visual_points:
            if i.collidepoint(Input.mouse_pos):
                CurvePoint.dragging = i
                break
        else: # no points were hit
            if Viewport.collidepoint(Input.mouse_pos):
                # create a new point
                new = CurvePoint(0, 0)
                main.add(new)
                visual_points.append(new)
                CurvePoint.dragging = new
                new.step()
    if ev.button == pg.BUTTON_RIGHT:
        # remove a point
        if len(visual_points) <= 2: # safeguard
            return
        for i in visual_points:
            if i.collidepoint(Input.mouse_pos):
                visual_points.remove(i)
                main.remove(i)
                refresh_points()
                break


def unclick_handler(ev):
    if ev.button == pg.BUTTON_LEFT:
        if CurvePoint.dragging is not None:
            CurvePoint.dragging.pulse_t = 0
            CurvePoint.dragging = None
            refresh_points()


def keyboard_handler(ev):
    if Viewport.editing_what is None:
        return
    #  vvvvvvvvvvvvvvv to allow fake events
    if ev == "_RETURN" or ev.key == pg.K_RETURN:
        # try/except can be replaced with some int.isfloat() but i cba
        try:
            val = float(Viewport.editing_text)
            val_name = Viewport.editing_what._value
            Viewport.set_value(val_name, val)
        except:
            pass
        Viewport.editing_what.color = "white"
        Viewport.editing_what = None
        return
    if ev.key == pg.K_ESCAPE:
        Viewport.editing_what.color = "white"
        Viewport.editing_what = None
        return
    if ev.key == pg.K_BACKSPACE:
        if Input.shift:
            Viewport.editing_text = ""
        Viewport.editing_text = Viewport.editing_text[:-1]
        return
    if ev.unicode:
        Viewport.editing_text += ev.unicode


Window.add_event_handler({
    pg.MOUSEBUTTONDOWN: click_handler,
    pg.MOUSEBUTTONUP: unclick_handler,
    pg.KEYDOWN: keyboard_handler,
})


Window.create(win_size, caption="Curve editor")
dt = Window.set_fps(fps)
Window.scene = main


# setting up color.hsva = (...)
color = pg.Color(0)

while Window.is_open:
    # labels
    label_x_from.text = f"X_min = {Viewport.x_from:.2f}"
    label_x_to.text = f"X_max = {Viewport.x_to:.2f}"
    label_y_from.text = f"Y_min = {Viewport.y_from:.2f}"
    label_y_to.text = f"Y_max = {Viewport.y_to:.2f}"
    if Viewport.editing_what is not None:
        prefix = Viewport.editing_what.text.split("=")[0] + "= "
        Viewport.editing_what.text = prefix + Viewport.editing_text

    # export button
    if export_button.collidepoint(Input.mouse_pos):
        export_button.color = (60, 60, 20)
        if Input.mouse_just_pressed[0]: # left
            print("my_curve = Curve([")
            x_ratio = (Viewport.x_to - Viewport.x_from)
            y_ratio = (Viewport.y_to - Viewport.y_from)
            x_offset = Viewport.x_from
            y_offset = Viewport.y_from
            for key, val in curve_points.items():
                x = key * x_ratio + x_offset
                y = val * y_ratio + y_offset
                print(f"    Point({x}, {y}),")
            print("])")
            export_label.text = "Exported to console!"
    else:
        export_button.color = (40, 40, 40)

    # updating the curve if dragging
    if CurvePoint.dragging is not None:
        refresh_points()

    # preview point
    time_unit = Viewport.x_to - Viewport.x_from
    x = Window.t / time_unit % 1
    y = 1 - curve.get(x)
    preview_point.update(x * Viewport.w, y * Viewport.h)

    # graph edge lines
    edge_l.p1.update(0, visual_points[0].y)
    edge_l.p2.update(visual_points[0])
    edge_r.p2.update(Viewport.w, visual_points[-1].y)
    edge_r.p1.update(visual_points[-1])

    # time unit line
    left_edge.x = win_size[0] - time_unit * 2 * fps

    # curve value history
    factor = min(max(100 - y*100, 0), 100)
    color.hsva = (200, 100, factor, 100)
    # evil hack to shift the trail surface left
    pg.draw.rect(trail.surface, color, (win_size[0]-2, 0, 5, 20))
    trail.surface.blit(trail.surface, (-2, 0))

    Window.finish_frame()
