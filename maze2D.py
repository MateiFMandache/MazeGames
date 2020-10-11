import tkinter as tk
from copy import deepcopy
import random
from tkinter import messagebox
from itertools import product

WIDTH = 800
HEIGHT = 600
MAX_ROWS = 99
MAX_COLUMNS = 133

root = tk.Tk()
entry_rows = tk.Entry(root)
entry_columns = tk.Entry(root)
entry_rows.insert(0, "20")
entry_columns.insert(0, "20")
label_rows = tk.Label(root, text="Number of rows:")
label_columns = tk.Label(root, text="Number of columns:")
label_rows.grid(row=0, column=0)
entry_rows.grid(row=0, column=1)
label_columns.grid(row=1, column=0)
entry_columns.grid(row=1, column=1)


def start_maze():
    global width, height
    ec = entry_columns.get()
    er = entry_rows.get()
    width = int(entry_columns.get()) if (ec.isnumeric and ec) else 20
    height = int(entry_rows.get()) if (er.isnumeric and er) else 20
    if width > MAX_COLUMNS:
        width = MAX_COLUMNS
    if height > MAX_ROWS:
        height = MAX_ROWS
    root.destroy()


button = tk.Button(root, text="Start maze", command=start_maze)
button.grid(row=2, column=0, columnspan=2)

root.mainloop()

root = tk.Tk()
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT)
canvas.pack()


def congratulations():
    messagebox.showinfo("Congratulations!", "You solved the maze, well done!")
    root.destroy()


class Maze(object):
    def __init__(self, width, height, wall, goal_position, player_position=(0, 0)):
        self.width = width
        self.height = height
        self.wall = wall
        self.goal = list(goal_position)
        self.player = list(player_position)
        self.cell_size = int(min((WIDTH - 2)/self.width, (HEIGHT - 2)/self.height))
        self.start_x = int((WIDTH - self.cell_size * self.width) / 2)
        self.start_y = int((HEIGHT - self.cell_size * self.height) / 2)

    def draw(self):
        canvas.create_line(self.start_x, self.start_y,
                           self.start_x + self.width * self.cell_size, self.start_y)
        canvas.create_line(self.start_x, self.start_y, self.start_x,
                           self.start_y + self.height * self.cell_size)
        for column in range(self.width):
            for row in range(self.height):
                if self.wall[row][column][0]:
                    canvas.create_line(self.start_x + column * self.cell_size,
                                       self.start_y + (row + 1) * self.cell_size,
                                       self.start_x + (column + 1) * self.cell_size,
                                       self.start_y + (row + 1) * self.cell_size)
                if self.wall[row][column][1]:
                    canvas.create_line(self.start_x + (column + 1) * self.cell_size,
                                       self.start_y + row * self.cell_size,
                                       self.start_x + (column + 1) * self.cell_size,
                                       self.start_y + (row + 1) * self.cell_size)

        canvas.create_oval(self.start_x + self.goal[0] * self.cell_size,
                           self.start_y + self.goal[1] * self.cell_size,
                           self.start_x + (self.goal[0] + 1) * self.cell_size,
                           self.start_y + (self.goal[1] + 1) * self.cell_size,
                           fill="blue", width=0)
        self.draw_player()

    def draw_player(self):
        colour = "green" if self.player == self.goal else "red"
        canvas.create_oval(self.start_x + self.player[0] * self.cell_size,
                           self.start_y + self.player[1] * self.cell_size,
                           self.start_x + (self.player[0] + 1) * self.cell_size,
                           self.start_y + (self.player[1] + 1) * self.cell_size,
                           fill=colour, width=0, tags="player")

    def down(self):
        if not self.wall[self.player[1]][self.player[0]][0]:
            self.player[1] += 1
            canvas.delete("player")
            self.draw_player()
            if self.player == self.goal:
                congratulations()

    def up(self):
        if self.player[1] >= 1:
            if not self.wall[self.player[1] - 1][self.player[0]][0]:
                self.player[1] -= 1
                canvas.delete("player")
                self.draw_player()
                if self.player == self.goal:
                    congratulations()

    def right(self):
        if not self.wall[self.player[1]][self.player[0]][1]:
            self.player[0] += 1
            canvas.delete("player")
            self.draw_player()
            if self.player == self.goal:
                congratulations()

    def left(self):
        if self.player[0] >= 1:
            if not self.wall[self.player[1]][self.player[0] - 1][1]:
                self.player[0] -= 1
                canvas.delete("player")
                self.draw_player()
                if self.player == self.goal:
                    congratulations()


def grow_maze(width, height):
    """
    Grow a maze by iteratively removing one of the panels bordering the
    player's connected region.
    :param width: number of columns
    :param height: number of rows
    :return: a tuple containing the wall, the goal position and the player position
    """
    # Initialise used array. This keeps track of which cells have been used
    row = [0] * width
    used = []
    for i in range(height):
        used.append(row.copy())
    used[0][0] = 1
    # Initialise array wall
    cell = [1, 1]
    row = []
    for i in range(width):
        row.append(cell.copy())
    wall = []
    for i in range(height):
        wall.append(deepcopy(row))
    # active walls will be the list of panels we're considering knocking down.
    active_panels = [[0, 0, 0], [0, 0, 1]]
    while active_panels:
        # knock down a panel
        knock_down = random.choice(active_panels)
        wall[knock_down[0]][knock_down[1]][knock_down[2]] = 0
        if used[knock_down[0]][knock_down[1]]:
            if knock_down[2] == 0:
                added_cell = [knock_down[0] + 1, knock_down[1]]
            else:
                assert knock_down[2] == 1
                added_cell = [knock_down[0], knock_down[1] + 1]
        else:
            added_cell = [knock_down[0], knock_down[1]]
        used[added_cell[0]][added_cell[1]] = 1

        def toggle(panel):
            if panel in active_panels:
                index = active_panels.index(panel)
                active_panels[index: index + 1] = []
            else:
                active_panels.append(panel)

        if added_cell[0] > 0:
            toggle([added_cell[0] - 1, added_cell[1], 0])
        if added_cell[1] > 0:
            toggle([added_cell[0], added_cell[1] - 1, 1])
        if added_cell[0] < height - 1:
            toggle([added_cell[0], added_cell[1], 0])
        if added_cell[1] < width - 1:
            toggle([added_cell[0], added_cell[1], 1])
    return wall, (width-1, height-1), (0, 0)


def percolate_maze(width, height):
    """
    Produce a maze by iteratively removing a panel at random if the removal
    doesn't produce a loop.
    :param width: number of columns
    :param height: number of rows
    :return: a tuple containing the wall, the goal position and the player position
    """
    # Initialise root function. This is a function with
    # root_f[cell1] = root_f[cell2] iff cell1 and cell2
    # are in the same connected component.
    root_f = []
    for i in range(height):
        row = []
        for j in range(width):
            row.append((i, j))
        root_f.append(row)
    # Initialise list of panels
    panel_list = []
    for i in range(height):
        for j in range(width):
            if i < height - 1:
                panel_list.append([i, j, 0])
            if j < width - 1:
                panel_list.append([i, j, 1])
    # initialise wall
    cell = [1, 1]
    row = []
    for i in range(width):
        row.append(cell.copy())
    wall = []
    for i in range(height):
        wall.append(deepcopy(row))
    # initialise dict giving the panels with each given root
    root_dict = {(i, j): [(i, j)] for i in range(height) for j in range(width)}
    # now for the iterative loop
    while panel_list:
        panel = random.choice(panel_list)
        panel_list.remove(panel)
        if panel[2] == 0:
            adjacent_cells = [panel[0:2], [panel[0] + 1, panel[1]]]
        else:
            assert panel[2] == 1
            adjacent_cells = [panel[0:2], [panel[0], panel[1] + 1]]
        root0 = root_f[adjacent_cells[0][0]][adjacent_cells[0][1]]
        root1 = root_f[adjacent_cells[1][0]][adjacent_cells[1][1]]
        if root0 != root1:
            # knock down wall
            wall[panel[0]][panel[1]][panel[2]] = 0
            # transfer cells with one root to the other root, depending
            # on which of them has fewer cells
            if len(root_dict[root0]) > len(root_dict[root1]):
                for (i, j) in root_dict[root1]:
                    root_f[i][j] = root0
                root_dict[root0].extend(root_dict[root1])
                del root_dict[root1]
            else:
                for (i, j) in root_dict[root0]:
                    root_f[i][j] = root1
                root_dict[root1].extend(root_dict[root0])
                del root_dict[root0]
    return wall, (width-1, height-1), (0, 0)


def generate_maze(width, height, method="percolate"):
    """
    Generates a maze using the method given
    :param width: number of columns
    :param height: number of rows
    :param method: The supported methods are
    "grow" and "percolate". Percolate is used as default since it tends to produce
    more interesting mazes.
    :return: a tuple containing the wall, the goal position and the player position
    """
    if method == "grow":
        return grow_maze(width, height)
    if method == "percolate":
        return percolate_maze(width, height)


wall, goal_pos, player_pos = generate_maze(width, height)
maze = Maze(width, height, wall, goal_pos, player_pos)
maze.draw()
root.bind("<Down>", lambda z: maze.down())
root.bind("<Up>", lambda z: maze.up())
root.bind("<Right>", lambda z: maze.right())
root.bind("<Left>", lambda z: maze.left())

root.mainloop()
