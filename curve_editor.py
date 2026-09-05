from apynimation import *

win_size = (1600, 900)
fps = 144


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


class CurvePoint(Point):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pulse_t = 999
        self.dragging = False

    def update(self, t=0):
        self.pulse_t += 50 * dt
        if self.dragging:
            self.pos.update(Input.mouse_pos)
            Viewport.keep_in_view(self.pos)

    def render(self, target):
        pg.draw.circle(target, "white", self.pos, 20, 1)
        pg.draw.circle(target, "white", self.pos, 5)
        if self.pulse_t < 50/3:
            radius = 15 * self.pulse_t ** 0.5
            width = int(50/3 - self.pulse_t + 1)
            pg.draw.circle(target, "white", self.pos, radius, width)

    def collidepoint(self, point):
        return self.pos.distance_to(point) < 20


main = Scene(win_size)
layer = main.create_layer()

preview_point = Point()
preview_circle = layer.add(Circle(preview_point, color="red", radius=7, width=0))

points = list(layer.add(
    CurvePoint(0, Viewport.h),
    CurvePoint(Viewport.w*0.5, Viewport.h*0.72),
    CurvePoint(Viewport.w, 0),
))
curve = Curve(points)

wireframe = Wireframe(points)
layer.add(wireframe)

edge_l = Line(Point(), Point())
edge_r = Line(Point(), Point())
layer.add(edge_l, edge_r)

trail = Sprite((0, win_size[1] - 20))
trail.surface = pg.Surface((win_size[0], 20))
layer.add(trail)

left_edge = Point(0, win_size[1]-25) # x gets set later in the code
right_edge = Point(win_size[0], win_size[1]-25)
unit_length = Line(left_edge, right_edge, width=3)
layer.add(unit_length)


font = pg.font.SysFont("consolas", 25)
label_x_from = Text(font, pos=(Viewport.w+30, 15))
label_x_to = Text(font, pos=(Viewport.w+350, 15))
label_y_from = Text(font, pos=(Viewport.w+30, 45))
label_y_to = Text(font, pos=(Viewport.w+350, 45))
labels = layer.add(label_x_from, label_x_to, label_y_from, label_y_to)

label_x_from._value = "x_from"
label_y_from._value = "y_from"
label_x_to._value = "x_to"
label_y_to._value = "y_to"


export_button = Rect(Point(Viewport.w + 30, 120), w=250, h=60)
export_button.update() # setting up .rect.center
button_origin = export_button.rect.center

font = pg.font.SysFont("consolas", 20)
export_label = Text(font, "Export curve points", pos=button_origin, align="center")
layer.add(export_button, export_label)


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
        for i in points:
            if i.collidepoint(Input.mouse_pos):
                i.dragging = True
                break
        else: # no points were hit
            if Input.shift:
                # create a new point
                new = CurvePoint()
                layer.add(new)
                points.append(new)
                new.dragging = True
                new.update()
                curve.update_points()
    if ev.button == pg.BUTTON_RIGHT:
        # remove a point
        if len(points) <= 2: # safeguard
            return
        for i in points:
            if i.collidepoint(Input.mouse_pos):
                points.remove(i)
                layer.objects.remove(i)
                curve.update_points()
                break


def unclick_handler(ev):
    if ev.button == pg.BUTTON_LEFT:
        for i in curve.points:
            if i.dragging:
                i.pulse_t = 0
                i.dragging = False
                curve.update_points()
                break


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
    label_x_from.text = f"X_min = {Viewport.x_from:.2f}"
    label_x_to.text = f"X_max = {Viewport.x_to:.2f}"
    label_y_from.text = f"Y_min = {Viewport.y_from:.2f}"
    label_y_to.text = f"Y_max = {Viewport.y_to:.2f}"
    if Viewport.editing_what is not None:
        prefix = Viewport.editing_what.text.split("=")[0] + "= "
        Viewport.editing_what.text = prefix + Viewport.editing_text

    if export_button.collidepoint(Input.mouse_pos):
        export_button.color = (60, 60, 20)
        if Input.mouse_just_pressed[0]: # left
            print("my_curve = Curve([")
            x_ratio = (Viewport.x_to - Viewport.x_from) / Viewport.w
            y_ratio = (Viewport.y_to - Viewport.y_from) / Viewport.h
            x_offset = Viewport.x_from
            y_offset = Viewport.y_from
            for i in points:
                x = i.pos.x * x_ratio + x_offset
                y = (Viewport.h - i.pos.y) * y_ratio + y_offset
                print(f"    Point({x}, {y}),")
            print("])")
            export_label.text = "Exported to console!"
    else:
        export_button.color = (40, 40, 40)

    time_unit = Viewport.x_to - Viewport.x_from
    left_edge.pos.x = win_size[0] - time_unit * 2 * fps

    x = (Window.t / time_unit % 1) * Viewport.w
    y = curve.get(x)
    preview_point.pos.update(x, y)
    edge_l.p1.pos.update(0, points[0].pos.y)
    edge_l.p2.pos.update(points[0].pos)
    edge_r.p2.pos.update(Viewport.w, points[-1].pos.y)
    edge_r.p1.pos.update(points[-1].pos)

    factor = min(max(100 - y*100 / Viewport.h, 0), 100)
    color.hsva = (200, 100, factor, 100)
    # evil hack to shift the trail surface left
    pg.draw.rect(trail.surface, color, (win_size[0]-2, 0, 5, 20))
    trail.surface.blit(trail.surface, (-2, 0))

    Window.finish_frame()
