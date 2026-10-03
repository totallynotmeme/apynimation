# a basic implementation of Minesweeper
#
# i wrote the first version in ~3 hours, so the code isn't the best,
# but it's pretty easily expandable and moddable
# TODO: variable running is unfinished/unused

from apynimation import *
from apynimation import ui
import random


print("""
CONTROLS:
R - reset board
Z - open a cell / expand numbered cell
C - mark cell as mine
""")


win_size = (1600, 900)
fps = 60

# paramaters
grid_size = (20, 12)
mine_count = 35
# visual size (in pixels), change this if the grid doesn't fit the window
cell_size = 65
cell_padding = 5

font = pg.font.SysFont("consolas", 30)
running = False

ui.default_theme.color = (50, 70, 150)
ui.default_theme.dark = pg.Color(20, 20, 20)
colortable = {
    0: (127, 127, 127),
    1: (100, 100, 255),
    2: (255, 255, 120),
    3: (255, 120, 120),
    4: (50, 50, 200),
    5: (150, 20, 20),
    6: (100, 255, 255),
    7: (255, 255, 255),
}

x_start = win_size[0]/2 - (cell_size + cell_padding) * grid_size[0] / 2
y_start = win_size[1]/2 - (cell_size + cell_padding) * grid_size[1] / 2
free_cells = grid_size[0] * grid_size[1] - mine_count


# safeguard. free_cells=0 works fine but has no point
if free_cells < 0:
    print(f"[FATAL] there are too many mines! Please remove at least {free_cells} mines")
    exit(1)


class Cell(ui.Button):
    opened = 0
    flagged = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.neighbours = []
        self.mine_state = None
        self.mine = None
        self.flag = False
        self.center = pg.Vector2(self.pos) + (cell_size/2, cell_size/2)
        self.label = Text(font, text="?", point=self.center, align="center")
        self.show_label = False
        self.open_t = -1

    def reset(self):
        self.mine_state = None
        self.open_t = -1
        self.mine = None
        self.flag = False
        self.show_label = False

    def step(self, t=0):
        super().step(t)
        if self.mine_state == -999:
            self.color = "red"
        elif self.mine_state is not None:
            self.color = self.theme.dark
        self.open_t -= 1
        if self.open_t == 0:
            self.open()

    def draw(self, target):
        super().draw(target)
        if self.mine_state == -999:
            # mine
            pg.draw.circle(target, "black", self.center, cell_size/2 - 5)
        elif self.show_label:
            # number
            self.label.step()
            self.label.draw(target)
        elif self.flag:
            # flag
            pg.draw.circle(target, (50, 200, 80), self.center, cell_size/3 - 5)

    def callback(self):
        # overwrite callback function so nothing happens on click.
        # TODO: make it work with mouse controls
        pass

    def open(self):
        global running
        if not running:
            # reroll first click
            for rigged in [self] + self.neighbours:
                if rigged.mine is None:
                    continue
                choices = list(mines.values())
                for _ in range(100): # give up after 100 tries
                    what = random.choice(choices)
                    if what.mine is not None:
                        continue
                    if what == rigged or what in rigged.neighbours:
                        continue
                    what.mine = rigged.mine
                    rigged.mine = None
                    break
            # continue as normal lol

        running = True
        if self.mine_state is not None:
            # open neighbour cells if nearby mines are marked
            if self.mine_state == 0:
                return
            if self.mine_state == sum(i.flag for i in self.neighbours):
                for i in self.neighbours:
                    if i.mine_state is None and not i.flag:
                        i.open()
            return

        if self.mine is not None:
            # lose
            self.mine_state = -999
            return

        # open cell
        Cell.opened += 1
        if self.flag:
            self.flag = False
            Cell.flagged -= 1

        # check neighbour cells to see what number to show
        nearby_mines_exist = False
        nearby_mines_val = 0
        for i in self.neighbours:
            if i.mine is not None:
                nearby_mines_exist = True
                nearby_mines_val += i.mine

        if nearby_mines_exist:
            self.mine_state = nearby_mines_val
            self.label.text = str(self.mine_state)
            self.label.color = colortable[self.mine_state % 8]
            self.show_label = True
        else:
            self.mine_state = 0
            # if no mines nearby, flood-open neighbour cells
            for i in self.neighbours:
                i.open_t = 5


scene = Scene(win_size)
Window.scene = scene
Layer.DISABLE_BUFFER = True

mines = {}
for x in range(grid_size[0]):
    pos_x = x * (cell_size + cell_padding) + x_start
    for y in range(grid_size[1]):
        pos_y = y * (cell_size + cell_padding) + y_start
        cell = Cell((pos_x, pos_y), (cell_size, cell_size))
        scene.add(cell)
        mines[(x, y)] = cell

# neighbour scan
for x in range(grid_size[0]):
    for y in range(grid_size[1]):
        table = [
            (x-1, y-1), (x, y-1), (x+1, y-1),
            (x-1, y  ),           (x+1, y  ),
            (x-1, y+1), (x, y+1), (x+1, y+1),
            # (x+1,y), (x-1,y), (x,y+1), (x,y-1),
            # uncomment the line above to enable a funny mod:
            # mines to the left/right/up/down are worth 2 points,
            # ones that are touching corners remain normal.
            # idea "borrowed" from https://store.steampowered.com/app/1865060/14/
        ]
        table = [i for i in table if 0 <= i[0] < grid_size[0] and 0 <= i[1] < grid_size[1]]
        table = [mines[i] for i in table]
        mines[(x, y)].neighbours = table

def generate():
    global running
    running = False
    Cell.opened = 0
    Cell.flagged = 0
    win_layer.active = False

    # reset all mines first
    for i in mines.values():
        i.reset()

    choices = list(mines.values())
    i = 0
    while i < mine_count:
        what = random.choice(choices)
        if what.mine:
            continue
        what.mine = 1
        i += 1


def keydown_callback(ev):
    if ev.key == pg.K_r:
        generate()
    if ev.key == pg.K_z:
        # open a cell
        for i in mines.values():
            if i.state == ui.STATE_HOVERING:
                if not i.flag:
                    i.open()
                break
    if ev.key == pg.K_c:
        # flag a cell
        for i in mines.values():
            if i.state == ui.STATE_HOVERING:
                if i.mine_state is None:
                    i.flag = not i.flag
                    Cell.flagged += i.flag * 2 - 1
                break


Window.add_event_handler({
    pg.KEYDOWN: keydown_callback,
})


mines_label = Text(font, pos=(10, 10))
scene.add(mines_label)


win_layer = scene.create_layer()
win_layer.add(Rect(Point(0, 0), Point(win_size), color=(50, 200, 50), width=10))
win_layer.active = False

generate()
Window.create(win_size, "Minesweeper at home")
dt = Window.set_fps(fps)

while Window.is_open:
    if Cell.opened == free_cells:
        # show the winning highlight
        win_layer.active = (Window.t % 1 > 0.5)
    mines_label.text = f"{Cell.flagged}/{mine_count}"
    Window.finish_frame()

# cleanup (it sometimes segfaults when quitting without this line)
for i in mines.values():
    i.neighbours = None
