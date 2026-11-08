from apynimation import *
from apynimation import logic
from apynimation.animate import *

Window.set_res((1600, 900))
Window.set_fps(60)
Window.create("Animation demo")


drivers = []
drivers.append(("SEP", 0))

for i in range(2, 10+1, 2):
    drivers.append((f"Towards, speed={i}", [Towards, i]))

drivers.append(("SEP", 120))

for i in range(5, 30+1, 5):
    i /= 10
    drivers.append((f"Linear, time={i}", [Linear, i]))


demo = Scene()
Window.scene = demo
animator = demo.add(Animator(), logic=True)


font = pg.font.SysFont("consolas", 30)
scroll_pos = Point()


x0 = 80
x1 = Window.res[0] - 120
pos_tape = logic.Tape([x1, x0])
pos_ticker = logic.Ticker(2)

color = pg.Color(0)

y = 50
points = []
for name, args in drivers:
    if name == "SEP":
        hue = args
        sat = 40
        y += 40
        continue

    slider_shift = Point(Window.center.x, y+40)
    animator.hook(slider_shift, "x", *args)
    points.append(slider_shift)
    slider_shift.x = x0

    color.hsva = (hue, sat, 90, 100)

    label = Text(font, name, pos=OffsetPoint(scroll_pos, (50, y)))
    line = Line(
        OffsetPoint(scroll_pos, (100, y+60)),
        OffsetPoint(scroll_pos, (Window.res[0]-100, y+60)),
        color = (127, 127, 127),
    )
    square = Rect(
        p1 = OffsetPoint(scroll_pos, slider_shift),
        w = 41, h = 41,
        color = pg.Color(color), # copying the color here
    )
    demo.add(label, line, square)
    y += 150
    sat = clamp(sat*1.1, 0, 100)

y_limit = -(y - Window.center.y)


@demo.event_handler
def on_mousewheel(ev):
    scroll_pos.y += ev.precise_y * 50
    scroll_pos.y = clamp(scroll_pos.y, y_limit, Window.center.y)


while Window.is_open:
    if pos_ticker.step():
        x = pos_tape.next()
        for i in points:
            i.x = x

    Window.finish_frame()
