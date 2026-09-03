from apynimation import *

win_size = (1600, 900)
fps = 144


# creating a custom class to reduce repetition
class UI_Button:
    _ind = 0
    font = pg.font.SysFont("consolas", 20)
    
    def __init__(self, name, scene):
        self.name = name
        self.scene = scene
        
        x = 110
        y = UI_Button._ind * 60 + 35
        center = Point(x, y)
        topleft = Point(x-100, y-25)
        self.rect = Rect(topleft, w=200, h=50)
        self.label = Text(font=UI_Button.font, text=name, point=center, align="center")
        UI_Button._ind += 1
    
    def update(self, t):
        if Window.scene == self.scene:
            self.rect.color = (75, 100, 150)
            self.label.text = f"> {self.name} <"
        elif self.rect.collidepoint(Input.mouse_pos):
            self.rect.color = (100, 100, 50)
            self.label.text = f"~ {self.name} ~"
            if Input.mouse_just_pressed[0]: # left
                Window.scene = self.scene
                scene_tape.set(self.scene) # scene_tape defined later
        else:
            self.rect.color = (50, 50, 50)
            self.label.text = self.name
        self.rect.update(t)
        self.label.update(t)
    
    def render(self, target):
        self.rect.render(target)
        self.label.render(target)


## about this demo
about_demo = Scene(win_size)
about_layer = about_demo.create_layer()
Window.global_objects.append(UI_Button("About", about_demo))

font = pg.font.SysFont("consolas", 35)
about_layer.add(Text(font, text="This is a simple interactive demo!", pos=(230, 20)))

lines = [
    "This abomination is a pygame-based library i made for myself to",
    "create simple interactive animations or small programs with basic UI.",
    "",
    "There's not a lot of features in the current version, but",
    "if you find this silly project useful and want to contribute,",
    "pull requests are open!",
    "",
    "You can switch scenes by clicking the buttons on the left,",
    "or with Tab (or Shift+Tab to cycle in the other direction)",
]
font = pg.font.SysFont("consolas", 25)
for ind, i in enumerate(lines):
    if i == "":
        continue
    y = ind * 35 + 100
    about_layer.add(Text(font, text=i, pos=(240, y)))


## cursor demo scene
cursor_demo = Scene(win_size)
cursor_layer = cursor_demo.create_layer()
Window.global_objects.append(UI_Button("Cursor", cursor_demo))

cursor_layer.add(Text(font, text="Try left clicking somewhere", pos=(230, 20)))

# trail
cursor_trail = Line(Point(), Point(), width=5)

def _update(t=0):
    cursor_trail.p1.pos.update(Input.mouse_pos)
    cursor_trail.p2.pos.update(Input.mouse_prev_pos)
cursor_trail.update = _update

cursor_layer.add(cursor_trail)

# click bubble
click_position = Point()
click_circle = cursor_layer.add(Circle(click_position, color=(0, 127, 255), radius=50))
click_radius = 999

click_limiter = Limiter(1/3)

def mouse_click_handler(ev):
    global click_radius
    if ev.button == pg.BUTTON_LEFT and click_limiter.call():
        click_position.pos.update(ev.pos)
        click_radius = 0


## 3d scene
donut_demo = Scene(win_size)
donut_layer = donut_demo.create_layer()
Window.global_objects.append(UI_Button("3D donut", donut_demo))

camera_data = {
    "focal_length": 350,
    "win_size": pg.Vector2(win_size),
    "camera_pos": pg.Vector3(0, 0, -100),
}
donut_points = []

# forming a donut with a bunch of circles
inner_up = pg.Vector2(75, 0) # r(small) of the torus / donut
for angle_x in range(0, 360, 360 // 15):
    r_add, z_offset = inner_up.rotate(angle_x)
    up = pg.Vector3(0, 250 + r_add, z_offset)
    for angle_z in range(0, 360, 360 // 15):
        pos = up.rotate_z(angle_z)
        a = donut_layer.add(Point3d(pos, data=camera_data))
        donut_points.append(a)
donut_layer.add(Wireframe(donut_points, closed=True))


## layers demo
layers_demo = Scene(win_size)
Window.global_objects.append(UI_Button("Layer effects", layers_demo))
font = pg.font.SysFont("consolas", 40)

layers_text_pos = pg.Vector2(250, 0) # using one Vector2 to replace sin() and cos()

# layers_demo_l0 = layers_demo.create_layer()
# layers_text_l0 = Text(font, "Invisible text???", pos=(700, 400))
# layers_demo_l0.add(layers_text_l0)

layers_demo_l1 = layers_demo.create_layer()
layers_text_l1 = Text(font, "Layer with smear effect")
layers_demo_l1.add(layers_text_l1)

layers_demo_l2 = layers_demo.create_layer()
layers_text_l2 = Text(font, "Layer with no effects")
layers_demo_l2.add(layers_text_l2)

# post-processing effects for layer 2
# (not really, as we're just modifying clear() function, but it still counts)
# NOTE: because we're filling the layer with opaque color, any layers behind it
# won't be visible. Uncomment _l0 lines above to see this issue in action.
# For real post-processing, you might want to overwrite .blit() function instead
filler = pg.Surface(win_size, pg.SRCALPHA)
filler.fill((0, 0, 0, 10))
def _clear():
    layers_demo_l1.surf.blit(filler, (0, 0))

layers_demo_l1.clear = _clear


## other stuff (only n-gons so far)
other_demo = Scene(win_size)
other_layer = other_demo.create_layer()
Window.global_objects.append(UI_Button("Other", other_demo))

center_point = Point(win_size)
center_point.pos /= 2
ngons = [
    CircleNgon(center_point, width=1, radius=50, sides=5),
    CircleNgon(center_point, width=3, radius=100, sides=6),
    CircleNgon(center_point, width=5, radius=150, sides=7),
    CircleNgon(center_point, width=2, radius=200, sides=8, color=(0, 127, 255)),
]
for i in ngons:
    other_layer.add(i)


# switching scenes with Tab
scene_tape = Tape(
    [about_demo, cursor_demo, donut_demo, layers_demo, other_demo],
    _ind=0 # we already have about_demo selected by default
)

def keyboard_handler(ev):
    if ev.key == pg.K_TAB:
        if Input.shift:
            Window.scene = scene_tape.prev()
        else:
            Window.scene = scene_tape.next()


Window.add_event_handler({
    pg.MOUSEBUTTONDOWN: mouse_click_handler,
    pg.KEYDOWN: keyboard_handler,
})


Window.create(win_size, caption="Basic UI demo")
Window.scene = about_demo
dt = Window.set_fps(fps)

while Window.is_open:
    # click bubble animation
    click_radius += 50 * dt
    if click_radius < 50/3:
        click_circle.radius = click_radius ** 1.5
        click_circle.width = int(50/3 - click_radius + 1)
    else:
        click_circle.radius = 0
    
    # spinning donut
    for i in donut_points:
        i.pos3d.rotate_x_ip(60 * dt)
        i.pos3d.rotate_z_ip(60 * dt)
    
    # moving the texts
    layers_text_pos.rotate_ip(60 * dt)
    layers_text_l1.pos.update(300, layers_text_pos.y + 400)
    layers_text_l2.pos.update(900, layers_text_pos.x + 400)
    
    # rotating the n-gon circles
    for i in ngons:
        spin = (i.sides - 6.5) * 45 * dt
        i.angle += spin
        # slow down when hovered
        if i.collidepoint(Input.mouse_pos):
            i.angle -= spin / 2
    
    Window.finish_frame()
