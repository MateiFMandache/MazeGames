from math import *
import numpy as np
import pygame
import random
import itertools
import tkinter as tk
from tkinter import messagebox


UNIT_SIZE = 300
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
MILLISECONDS_PER_FRAME = 33
ANGLE_STEP = 0.03
TRANSLATION_STEP = 0.03


def random_colour():
    red_component = random.randint(0, 255)
    green_component = random.randint(0, 255)
    blue_component = random.randint(0, 255)
    return red_component, green_component, blue_component


def rotation_matrix(axis, angle):
    if axis == "x":
        return np.array([[1, 0, 0], [0, cos(angle), -sin(angle)], [0, sin(angle), cos(angle)]])
    if axis == "y":
        return np.array([[cos(angle), 0, -sin(angle)], [0, 1, 0], [sin(angle), 0, cos(angle)]])
    if axis == "z":
        return np.array([[cos(angle), -sin(angle), 0], [sin(angle), cos(angle), 0], [0, 0, 1]])


def screen_position(spatial_position):
    """
    Draw as an observer sitting at the origin projecting things onto
    the z = 1 plane. Returns canvas coordinates ready for drawing.
    """
    x, y, z = tuple(spatial_position)
    projected_x = x/z
    projected_y = y/z
    canvas_x = 400 + UNIT_SIZE*projected_x
    canvas_y = 300 - UNIT_SIZE*projected_y
    return canvas_x, canvas_y


def in_view(spatial_position):
    return spatial_position[2] > 0


class Goal(object):
    def __init__(self, position):
        self.position = position

    def __abs__(self):
        """
        Gives the distance to the centre of the goal
        """
        return np.linalg.norm(self.position)

    def __lt__(self, other):
        """
        Overload < operator to avoid errors when sorting.
        See draw method of maze.
        """
        return False

    def rotate(self, rot_matrix):
        self.position = np.matmul(self.position, rot_matrix)

    def translate(self, translation_vector):
        self.position = self.position + translation_vector

    def draw(self, surface):
        if in_view(self.position):
            pygame.draw.circle(surface, WHITE, (int(screen_position(self.position)[0]),
                                                int(screen_position(self.position)[1])),
                               int(UNIT_SIZE*0.8/(2*abs(self))))

    def win(self):
        """
        The game is won if the goal is less than 0.4 away
        """
        return abs(self) < 0.4


class Panel(object):
    """
    A panel object is a square, with vertices given as numpy arrays
    """
    def __init__(self, vertices, colour):
        self.vertices = vertices
        self.colour = colour

    def rotate(self, rot_matrix):
        self.vertices = [np.matmul(vertex, rot_matrix) for vertex in self.vertices]

    def __abs__(self):
        """
        Gives the distance to the centre of the panel
        """
        return np.linalg.norm(self.vertices[0] + self.vertices[2]) / 2

    def __lt__(self, other):
        """
        Overload < operator to avoid errors when sorting.
        See draw method of maze.
        """
        return False

    def translate(self, translation_vector):
        self.vertices = [vertex + translation_vector for vertex in self.vertices]

    def is_blocking_forwards(self):
        """
        Returns True if panel is blocking a forward movement of
        TRANSLATION_STEP
        """
        v = self.vertices[0]
        w1 = self.vertices[1]-v
        w2 = self.vertices[3]-v
        matrix = np.array([w1[0:2], w2[0:2]])
        try:
            inverse = np.linalg.inv(matrix)
            coefficients = np.matmul(-v[0:2], inverse)
            if 0 < coefficients[0] < 1:
                if 0 < coefficients[1] < 1:
                    if 0 < np.dot(coefficients, np.array([w1[2], w2[2]])) + v[2] <= TRANSLATION_STEP:
                        return True
            return False
        except np.linalg.LinAlgError:
            return False

    def is_blocking_backwards(self):
        """
        Returns True if panel is blocking a backward movement of
        TRANSLATION_STEP
        """
        v = self.vertices[0]
        w1 = self.vertices[1]-v
        w2 = self.vertices[3]-v
        matrix = np.array([w1[0:2], w2[0:2]])
        try:
            inverse = np.linalg.inv(matrix)
            coefficients = np.matmul(-v[0:2], inverse)
            if 0 < coefficients[0] < 1:
                if 0 < coefficients[1] < 1:
                    if 0 > np.dot(coefficients, np.array([w1[2], w2[2]])) + v[2] >= -TRANSLATION_STEP:
                        return True
            return False
        except np.linalg.LinAlgError:
            return False

    def all_in_view(self):
        """
        Returns True if all vertices are in view
        """
        for vertex in self.vertices:
            if not in_view(vertex):
                return False
        return True

    def in_view(self):
        """
        Returns True if at least one vertex is in view
        """
        for vertex in self.vertices:
            if in_view(vertex):
                return True
        return False

    def draw(self, surface):
        if self.in_view():
            # We only draw if we are in view
            point_list = []
            if self.all_in_view():
                for vertex in self.vertices:
                    point_list.append(screen_position(vertex))
            else:
                # This is the tricky case. We start off by finding the
                # range of vertices which are in view
                # we work with indices mod 4, so sixth vertex is considered the
                # same as the second vertex.
                is_viewed = [in_view(vertex) for vertex in self.vertices]
                inv = is_viewed.index(False)
                for i in range(1, 4):
                    if is_viewed[(inv+i) % 4]:
                        first_in_view = (inv+i)
                        break
                for i in range(0, 3):
                    if not is_viewed[(first_in_view + i + 1) % 4]:
                        last_in_view = first_in_view + i
                        break
                # the first and last vertices in view should have infinite rays
                # coming off them. We use very long rays as a stand-in.
                # since the view field is small, the difference shouldn't be noticeable.
                # We first need to find the z=0 intercepts
                v0 = self.vertices[first_in_view % 4]
                v1 = self.vertices[(first_in_view - 1) % 4]
                first_line_intercept = v0 + (v1-v0) * ((v0[2])/(v0[2] - v1[2]))
                first_ray_xy_direction = first_line_intercept[0:2]
                normalised_first_ray_xy_direction = (first_ray_xy_direction /
                                                     np.linalg.norm(first_ray_xy_direction))
                # flip sign of y coordinate to prepare for screen
                normalised_first_ray_xy_direction[1] *= -1
                point_list.append(tuple(np.array((400, 300)) + normalised_first_ray_xy_direction*10_000))
                # Now go round the points that are in view
                for i in range(first_in_view, last_in_view+1):
                    point_list.append(screen_position(self.vertices[i % 4]))
                # Now for the other infinite ray
                v2 = self.vertices[last_in_view % 4]
                v3 = self.vertices[(last_in_view + 1) % 4]
                last_line_intercept = v2 + (v3 - v2) * ((v2[2]) / (v2[2] - v3[2]))
                last_ray_xy_direction = last_line_intercept[0:2]
                normalised_last_ray_xy_direction = (last_ray_xy_direction /
                                                    np.linalg.norm(last_ray_xy_direction))
                # flip sign of y coordinate to prepare for screen
                normalised_last_ray_xy_direction[1] *= -1
                point_list.append(tuple(np.array((400, 300)) + normalised_last_ray_xy_direction * 10_000))
            pygame.draw.polygon(surface, self.colour, point_list)


class Maze(object):
    def __init__(self, panel_list, goal_location):
        self.panels = panel_list
        self.goal = Goal(goal_location)

    def rotate(self, rot_matrix):
        for panel in self.panels:
            panel.rotate(rot_matrix)
        self.goal.rotate(rot_matrix)

    def translate(self, translation_vector):
        for panel in self.panels:
            panel.translate(translation_vector)
        self.goal.translate(translation_vector)

    def is_blocking_forwards(self):
        """
        Returns True if a forward movement of TRANSLATION_STEP is blocked
        """
        for panel in self.panels:
            if panel.is_blocking_forwards():
                return True
        return False

    def is_blocking_backwards(self):
        """
        Returns True if a backward movement of TRANSLATION_STEP is blocked
        """
        for panel in self.panels:
            if panel.is_blocking_backwards():
                return True
        return False

    def win(self):
        return self.goal.win()

    def draw(self, surface):
        surface.fill(BLACK)
        # draw panels and goal in inverse order of closeness. abs gives
        # the distance to the centre.
        object_list = self.panels + [self.goal]
        normed_object_list = [(abs(obj), obj) for obj in object_list]
        # In order to sort tuples without error in cases where two
        # objects have same norm, we overloaded < to be able to compare
        # panels and goals.
        normed_object_list.sort()
        normed_object_list.reverse()
        sorted_object_list = [tup[1] for tup in normed_object_list]
        for obj in sorted_object_list:
            obj.draw(surface)
        pygame.display.update()


def adjacent_panel(position_tuple, index):
    """
    Creates a panel in front of the position given by position_tuple
    as approached from the direction given by index
    """
    position_vector = np.array(position_tuple)
    # Create a panel and then translate it
    if index == 0:
        panel = Panel([np.array((-0.5, -0.5, -0.5)),
                       np.array((-0.5, 0.5, -0.5)),
                       np.array((-0.5, 0.5, 0.5)),
                       np.array((-0.5, -0.5, 0.5))], random_colour())
    elif index == 1:
        panel = Panel([np.array((-0.5, -0.5, -0.5)),
                       np.array((0.5, -0.5, -0.5)),
                       np.array((0.5, -0.5, 0.5)),
                       np.array((-0.5, -0.5, 0.5))], random_colour())
    else:
        assert index == 2
        panel = Panel([np.array((-0.5, -0.5, -0.5)),
                       np.array((0.5, -0.5, -0.5)),
                       np.array((0.5, 0.5, -0.5)),
                       np.array((-0.5, 0.5, -0.5))], random_colour())
    panel.translate(position_vector)
    return panel


def create_maze(width, height, depth, clear_steps, goal_postition):
    """
    Creates a maze with the given dimensions and the given clear steps.
    """
    panel_list = []
    for tup in itertools.product(range(width), range(height), range(depth)):
        for index in range(3):
            # Create panels in front of the cell given by tup,
            # In the direction specified by index,
            # As long as it is not one of the clear steps
            if (tup, index) not in clear_steps:
                panel_list.append(adjacent_panel(tup, index))
            # For the cells on the back edges, we also need to create
            # panels behind those cells in the specified direction.
            if index == 0:
                if tup[index] == width - 1:
                    new_tup = tuple(np.array(tup) + np.array((1, 0, 0)))
                    panel_list.append(adjacent_panel(new_tup, index))
            elif index == 1:
                if tup[index] == height - 1:
                    new_tup = tuple(np.array(tup) + np.array((0, 1, 0)))
                    panel_list.append(adjacent_panel(new_tup, index))
            else:
                assert index == 2
                if tup[index] == depth - 1:
                    new_tup = tuple(np.array(tup) + np.array((0, 0, 1)))
                    panel_list.append(adjacent_panel(new_tup, index))
    maze = Maze(panel_list, goal_postition)
    maze.translate(np.array((0, 0, 2)))
    return maze


def predefined_maze():
    clear_steps = [
        ((0, 0, 0), 2),
        ((0, 0, 1), 2),
        ((0, 0, 2), 2),
        ((0, 1, 2), 1),
        ((1, 0, 2), 0),
        ((1, 0, 0), 0),
        ((2, 0, 0), 0),
        ((2, 0, 1), 2),
        ((2, 0, 2), 2),
        ((0, 1, 1), 1),
        ((0, 2, 1), 1),
        ((0, 2, 2), 2),
        ((1, 2, 2), 0),
        ((1, 2, 2), 1),
        ((0, 2, 1), 2),
        ((1, 2, 0), 0),
        ((1, 2, 0), 1),
        ((1, 1, 0), 0),
        ((1, 2, 1), 0),
        ((2, 2, 1), 0),
        ((2, 2, 1), 2),
        ((2, 2, 0), 1),
        ((2, 2, 2), 2),
        ((2, 2, 2), 1),
        ((2, 1, 2), 2),
        ((2, 1, 1), 0),
        ((1, 1, 1), 1)
    ]
    goal_position = np.array((1, 0, 1))
    return create_maze(3, 3, 3, clear_steps, goal_position)


def procedurally_generated_maze(width, height, depth, goal_in_opposite_corner):
    clear_steps = [((0, 0, 0), 2)]
    # Initialise root function. This is a function with
    # root_f[cell1] = root_f[cell2] iff cell1 and cell2
    # are in the same connected component.
    root_f = []
    for i in range(width):
        body = []
        for j in range(height):
            row = []
            for k in range(depth):
                row.append((i, j, k))
            body.append(row)
        root_f.append(body)
    # Initialise list of panels.
    # These are the panels we might knock down
    panel_list = []
    for i in range(width):
        for j in range(height):
            for k in range(depth):
                if i > 0:
                    panel_list.append(((i, j, k), 0))
                if j > 0:
                    panel_list.append(((i, j, k), 1))
                if k > 0:
                    panel_list.append(((i, j, k), 2))
    while panel_list:
        next_panel = random.choice(panel_list)
        index = panel_list.index(next_panel)
        panel_list[index:index + 1] = []
        # cell1 and cell0 are the cells either side of the panel
        cell1 = next_panel[0]
        intermediary = list(cell1)
        intermediary[next_panel[1]] -= 1
        cell0 = tuple(intermediary)
        component1 = root_f[cell1[0]][cell1[1]][cell1[2]]
        component0 = root_f[cell0[0]][cell0[1]][cell0[2]]
        if component0 != component1:
            # If the cells are in different connected components
            # knock down the panel
            clear_steps.append(next_panel)
            # update root_f
            for i in range(width):
                for j in range(height):
                    for k in range(depth):
                        if root_f[i][j][k] == component1:
                            root_f[i][j][k] = component0
    if goal_in_opposite_corner:
        goal_position = np.array((width-1, height-1, depth-1))
    else:
        # We now put the goal in the furthest place
        # Initialise distance function
        distance_f = []
        for i in range(width):
            body = []
            for j in range(height):
                row = [None] * depth
                body.append(row)
            distance_f.append(body)
        distance_f[0][0][0] = 1
        running = True
        while running:
            # we carry on running if we computed any additional distances in
            # the previous loop.
            running = False
            # do not use the first panel, namely ((0, 0, 0), 2)
            for panel in clear_steps[1:]:
                # get the two cells either side of the panel
                cell1 = panel[0]
                intermediary = list(cell1)
                intermediary[panel[1]] -= 1
                cell0 = tuple(intermediary)
                distance1 = distance_f[cell1[0]][cell1[1]][cell1[2]]
                distance0 = distance_f[cell0[0]][cell0[1]][cell0[2]]
                # if only one cell had it's distance computed so far,
                # set the distance of the other to be one more than the
                # previously computed distance.
                if distance0 is None and distance1 is not None:
                    distance_f[cell0[0]][cell0[1]][cell0[2]] = distance1 + 1
                    running = True
                if distance1 is None and distance0 is not None:
                    distance_f[cell1[0]][cell1[1]][cell1[2]] = distance0 + 1
                    running = True
        record_distance = 1
        champion_position = (0, 0, 0)
        for i in range(width):
            for j in range(height):
                for k in range(depth):
                    if distance_f[i][j][k] > record_distance:
                        record_distance = distance_f[i][j][k]
                        champion_position = (i, j, k)
        goal_position = np.array(champion_position)
    return create_maze(width, height, depth, clear_steps, goal_position)


class GameOver(Exception):
    pass


def congratulations():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Maze complete", "Congratulations, you completed the maze")
    root.destroy()


def instructions():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Maze instructions",
                        "Find the white sphere.\nUse up and down to move, and w, a, s, d, q, e to turn")
    root.destroy()


def play_maze(maze):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    maze.draw(screen)
    my_font = pygame.font.SysFont("Arial", 48)
    instructions1 = my_font.render("Find the white sphere", 1, WHITE)
    instructions2 = my_font.render("Use up and down to move", 1, WHITE)
    instructions3 = my_font.render("Use w, a, s, d, q and e to turn", 1, WHITE)
    screen.blit(instructions1, (165, 400))
    screen.blit(instructions2, (122, 460))
    screen.blit(instructions3, (85, 520))
    pygame.display.update()

    quited = False
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quited = True
                waiting = False
            if event.type == pygame.KEYDOWN:
                waiting = False

    while not quited:
        pygame.time.delay(MILLISECONDS_PER_FRAME)
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise GameOver
        except GameOver:
            break

        keys = pygame.key.get_pressed()
        if keys[pygame.K_i]:
            instructions()
        if keys[pygame.K_w]:
            maze.rotate(rotation_matrix("x", -ANGLE_STEP))
        if keys[pygame.K_s]:
            maze.rotate(rotation_matrix("x", ANGLE_STEP))
        if keys[pygame.K_d]:
            maze.rotate(rotation_matrix("y", -ANGLE_STEP))
        if keys[pygame.K_a]:
            maze.rotate(rotation_matrix("y", ANGLE_STEP))
        if keys[pygame.K_e]:
            maze.rotate(rotation_matrix("z", -ANGLE_STEP))
        if keys[pygame.K_q]:
            maze.rotate(rotation_matrix("z", ANGLE_STEP))
        if keys[pygame.K_UP]:
            if not maze.is_blocking_forwards():
                maze.translate(np.array((0, 0, -TRANSLATION_STEP)))
                if maze.win():
                    congratulations()
                    break
        if keys[pygame.K_DOWN]:
            if not maze.is_blocking_backwards():
                maze.translate(np.array((0, 0, TRANSLATION_STEP)))
                if maze.win():
                    congratulations()
                    break
        maze.draw(screen)

    pygame.quit()


def random_maze_settings():
    root_settings = tk.Tk()
    root_settings.title("Choose size")
    tk.Label(root_settings, text="width").grid(row=0, column=0)
    tk.Label(root_settings, text="height").grid(row=1, column=0)
    tk.Label(root_settings, text="depth").grid(row=2, column=0)
    width_entry = tk.Entry(root_settings)
    height_entry = tk.Entry(root_settings)
    depth_entry = tk.Entry(root_settings)
    width_entry.grid(row=0, column=1)
    height_entry.grid(row=1, column=1)
    depth_entry.grid(row=2, column=1)
    width_entry.insert(0, "3")
    height_entry.insert(0, "3")
    depth_entry.insert(0, "3")

    goal_type = tk.StringVar()
    goal_type.set("Goal in opposite corner")
    tk.OptionMenu(root_settings, goal_type, "Goal in opposite corner",
                  "Goal down longest path").grid(row=3, column=0, columnspan=2)

    def start_random_maze():
        width_str = width_entry.get()
        height_str = height_entry.get()
        depth_str = depth_entry.get()
        root_settings.destroy()
        opposite_corner = True if goal_type.get() == "Goal in opposite corner" else False
        width = int(width_str) if (width_str.isnumeric() and width_str) else 3
        height = int(height_str) if (height_str.isnumeric() and height_str) else 3
        depth = int(depth_str) if (depth_str.isnumeric() and depth_str) else 3
        maze = procedurally_generated_maze(width, height, depth, opposite_corner)
        play_maze(maze)

    tk.Button(root_settings, text="Go", command=start_random_maze).grid(row=4, column=0, columnspan=2)


def main():
    root = tk.Tk()
    root.title("Choose type")
    maze_type = tk.StringVar()
    maze_type.set("Built-in maze")
    tk.OptionMenu(root, maze_type, "Built-in maze", "Randomly generate maze").pack()

    def start_maze():
        if maze_type.get() == "Built-in maze":
            maze = predefined_maze()
            root.destroy()
            play_maze(maze)
        else:
            assert maze_type.get() == "Randomly generate maze"
            root.destroy()
            random_maze_settings()

    tk.Button(root, text="Go", command=start_maze).pack()
    root.mainloop()


if __name__ == "__main__":
    main()
