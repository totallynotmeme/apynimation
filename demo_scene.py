from apynimation import *
from math import sin


win_size = (1600, 900)
fps = 144

# used for the blur effect. might make this into a Layer subclass later(?)
filler = pg.Surface(win_size, pg.SRCALPHA)
filler.fill((0, 0, 0, 10))

main = Scene(win_size)


ground_data = {
    "focal_length": 250,
    "win_size": pg.Vector2(win_size),
    "camera_pos": pg.Vector3(0, -50, 23),
}

ground = main.create_layer()
ground.surf = pg.Surface(main.size)
ground.clear = lambda: ground.surf.blit(filler, (0, 0))
ground.blit = lambda target: target.blit(ground.surf, (0, 0), None, pg.BLEND_ADD)

ground_points = [
    Point3d(x*60+30, 0, z*20, data=ground_data)
    for x in range(-10, 10)
    for z in range(-10, 10)
]
color = (0, 127, 255)

for z in range(20):
    inds = [z + x*20 for x in range(20)]
    ground.add(Wireframe([ground_points[i] for i in inds], color))
for x in range(20):
    inds = [z + x*20 for z in range(20)]
    ground.add(Wireframe([ground_points[i] for i in inds], color))



cube_data = {
    "focal_length": 250,
    "win_size": pg.Vector2(win_size),
    "camera_pos": pg.Vector3(0, 0, -100),
}

things = main.create_layer()

# cube
cube_points = [
    Point3d(x*100, y*100, z*100, data=cube_data)
    for x in (-1, 1)
    for y in (-1, 1)
    for z in (-1, 1)
]
edges = [
    (0, 1), (2, 3), (4, 5), (6, 7),
    (0, 2), (1, 3), (4, 6), (5, 7),
    (0, 4), (1, 5), (2, 6), (3, 7),
]
for i, j in edges:
    things.add(Line(cube_points[i], cube_points[j], width=3))

# sun-ish thing
sun_point = Point(80, 65)
sun_color = "yellow"
sun_sides = 8
sun_angle = 0

sun_circle_obj = CircleNgon(
    center_point = sun_point,
    color = sun_color,
    sides = sun_sides,
    radius = 33,
    width = 3
)
sun_update_t = 0 # todo: make a Ticker() to do this??
# sun_ticker = Ticker(step=0.3)
sun_angle_step = 360 / sun_sides

things.add(sun_circle_obj)
sun_rays = []
for i in range(sun_sides):
    line_angle = i * sun_angle_step + sun_angle
    pos1 = sun_point.pos + pg.Vector2(0, -40).rotate(line_angle)
    pos2 = sun_point.pos + pg.Vector2(0, -50).rotate(line_angle)
    sun_line = Line(Point(*pos1), Point(*pos2), color=sun_color, width=3)
    sun_rays.append(sun_line)
    things.add(sun_line)


# todo: move the window handling logic into a Window() class(?)
pg.init()
pg.display.set_caption("Test scene")
canvas = pg.display.set_mode(win_size)
clock = pg.time.Clock()

run = True
while run:
    ## animation
    # cube
    for i in cube_points:
        i.pos3d.rotate_y_ip(60/fps)
    
    cube_data["camera_pos"].y -= sin(main.t) * 69 / fps
    
    # ground
    for i in ground_points:
        i.pos3d.y += sin(i.pos3d.x + id(i) + main.t * 3) * 10 / fps
    
    ground_data["camera_pos"].z += 30/fps
    if ground_data["camera_pos"].z >= 42:
        ground_data["camera_pos"].z -= 20
        # shifting the point positions too
        for z_from in range(1, 20):
            z_to = z_from-1
            for x in range(20):
                p1 = ground_points[z_from + x * 20]
                p2 = ground_points[z_to + x * 20]
                p2.pos3d.y = p1.pos3d.y
        # random values for the last layer
        for x in range(20):
            ground_points[x*20 + 19].pos3d.y = 0
    
    # sun
    # if sun_ticker(main.t):
    sun_update_t -= 1/fps
    if sun_update_t < 0:
        sun_update_t = 0.3
        sun_circle_obj.angle += 17
        for ind, i in enumerate(sun_rays):
            line_angle = ind * sun_angle_step + sun_angle - main.t*30
            pos1 = sun_point.pos + pg.Vector2(0, -40).rotate(line_angle)
            pos2 = sun_point.pos + pg.Vector2(0, -50).rotate(line_angle)
            i.p1.pos.update(pos1)
            i.p2.pos.update(pos2)
    
    # actual rendering
    canvas.fill("black")
    main.render(canvas)
    
    pg.display.flip()
    clock.tick(fps)
    
    main.t += 1/fps
    
    for ev in pg.event.get():
        if ev.type == pg.QUIT:
            run = False
            break

pg.quit()
