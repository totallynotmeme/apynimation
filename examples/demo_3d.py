# !!! not a finished demo !!!
# currently this is just a test, not a functional / interesting demo,
# but feel free to take a look or mess around for now.
# why am i not using OpenGL for 3d graphics? well... it's fun lol
#
# the commented spaghetti are leftover from testing,
# and will be cleaned up later


from apynimation import *
from apynimation.three_d import *


Window.set_res((1600, 900))
Window.set_fps(60)
Window.create("Demo scene")

half_win_res = pg.Vector2(Window.res) / 2


world = Scene()
Window.scene = world


donut_points = []
# forming a donut with a bunch of circles
#"""
b = None
inner_up = pg.Vector2(10, 0) # r(small) of the torus / donut
for angle_x in range(0, 360, 360 // 15):
    r_add, z_offset = inner_up.rotate(angle_x)
    up = pg.Vector3(0, 25 + r_add, z_offset)
    for angle_z in range(0, 360, 360 // 15):
        pos = up.rotate_z(angle_z)
        a = Point3d(pos)
        if b is not None:
            world.add(Line3d(a, b))
        b = a
        donut_points.append(a)
#world.add(Wireframe(donut_points, closed=True))
"""
a = Point3d(0, 0, 0)
b = Point3d(10, 10, 10)
c = Point3d(-5, 9, 11)
world.add(Line3d(a, b))
world.add(Line3d(b, c))
"""

# rotation markers
rot_marker = Point()

range_marker_x = Rect((half_win_res.x-180, 0), w=360, h=20, color=(63, 63, 63))
range_marker_y = Rect((0, half_win_res.y-90), w=20, h=180, color=(63, 63, 63))
marker_x = Line(Point(0, 0), Point(0, 50), width=5)
marker_y = Line(Point(0, 0), Point(50, 0), width=5)
world.add(range_marker_x, range_marker_y, marker_x, marker_y)


# TODO: fix
Window.finish_frame()

while Window.is_open:
    # player controls
    motion_dir = pg.Vector3(
        Input.keyboard_keys[pg.K_d] - Input.keyboard_keys[pg.K_a],
        Input.keyboard_keys[pg.K_c] - Input.keyboard_keys[pg.K_z],
        Input.keyboard_keys[pg.K_w] - Input.keyboard_keys[pg.K_s],
    )
    rotation_dir = pg.Vector3(
        Input.keyboard_keys[pg.K_LEFT] - Input.keyboard_keys[pg.K_RIGHT],
        Input.keyboard_keys[pg.K_DOWN] - Input.keyboard_keys[pg.K_UP],
        0 #Input.keyboard_keys[pg.K_q] - Input.keyboard_keys[pg.K_e],
        # TODO: roll ^^^
    )
    motion_dir.rotate_y_ip(-default_camera.rot.x)

    speed = 30
    rot_speed = 90
    if Input.shift:
        speed = 90
        rot_speed = 180
    if Input.ctrl:
        speed /= 10
        rot_speed /= 10

    default_camera.pos += motion_dir * speed * Window.dt
    default_camera.rot += rotation_dir * rot_speed * Window.dt
    default_camera.rot.y = min(max(default_camera.rot.y, -89), 89)

    # updating the ui
    rot_marker.x = (default_camera.rot.x + 180) % 360 - 180
    rot_marker.y = -default_camera.rot.y
    rot_marker += half_win_res

    marker_x.p1.x = rot_marker.x
    marker_x.p2.x = rot_marker.x
    marker_y.p1.y = rot_marker.y
    marker_y.p2.y = rot_marker.y

    # spinning the donut
    for i in donut_points:
        i.pos3d.rotate_x_ip(60 * Window.dt)
        i.pos3d.rotate_z_ip(60 * Window.dt)

    Window.finish_frame()

