# original stuff

# import PySimpleGUI as sg
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import animation, rc
from IPython.display import HTML
matplotlib.use('Agg')
import os

EMPTY = 0
NON_INFECTED = 1
INFECTED = 2
CURED = 3


def covid_random_grid(dim, p_non_infected, p_infected, seed):
    """ Initialize a random grid of dim x dim random values

    Args:
        dim (int): dimensions for grid (will be square so x = y = dim)
        p_alive_feeder (float): probability of a live feeder cell on grid
        p_alive_predator (float): probability of a live predator cell on grid
        seed (int): seed for np.random.choice

    Returns:
        grid (numpy matrix): dim x dim numpy matrix populated with live and dead cells

    """
    np.random.seed(seed)
    possible_values = [INFECTED, EMPTY, NON_INFECTED]
    probabilities = [p_infected, 1 - (p_infected + p_non_infected), p_non_infected]

    array = np.random.choice(possible_values, dim * dim, p=probabilities).reshape(dim, dim)

    # have to set one tile to cured so the color shows up
    # this person ate the first bat i guess
    array[0, 0] = CURED
    return array


def get_neighbors(row, column, grid):
    """ Get the neighboring cells
    excluding any that might be out of bounds

    Args:
        row (int): row of cell
        column (int): column of cell
        grid (np matrix): matrix of all cells

    Returns:
        neighbors (list): list of adjacent cells

    Example:
    >>> get_neighbors(2,2, random_grid(4,.3,.3,1)) #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [2, 2, 0, 0, 0, 1, 2, 0]
    """
    neighbors = []
    # look at the row above
    if row != 0:
        for col in range(column - 1, column + 2):
            if col < 0 or col >= grid.shape[0]:
                continue
            neighbors.append(grid[row - 1, col])
    # look at current row:
    for col in range(column - 1, column + 2):
        if col < 0 or col >= grid.shape[0] or col == column:
            continue
        neighbors.append(grid[row, col])
    # look at above row
    if row != grid.shape[0] - 1:
        for col in range(column - 1, column + 2):
            if col < 0 or col >= grid.shape[0]:
                continue
            neighbors.append(grid[row + 1, col])

    return neighbors


def covid_count_infected_neighbors(row, column, grid):
    """ Count how many living feeder neighbors exist

    Args:
        row (int): row of cell
        column (int): column of cell
        grid (np matrix): matrix of all cells

    Returns:
        living_count (int): number of living feeder neighbors

    Example:
    >>> count_living_neighbors_feeder(2,2, random_grid(4,.3,.3,1)) #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    3
    """
    neighbors = get_neighbors(row, column, grid)
    count = 0
    for neighbor in neighbors:
        if neighbor == INFECTED:
            count += 1
    return count


def covid_get_swappable(row, column, grid):
    """ Get the neighboring cells
    excluding any that might be out of bounds

    Args:
        row (int): row of cell
        column (int): column of cell
        grid (np matrix): matrix of all cells

    Returns:
        neighbors (list): list of adjacent cells
    """
    rows = []
    cols = []
    # look at the row above
    if row is not 0:
        for col in range(column - 1, column + 2):
            if col < 0 or col >= grid.shape[0]:
                continue
            rows.append(row - 1)
            cols.append(col)
    # look at current row:
    for col in range(column - 1, column + 2):
        if col < 0 or col >= grid.shape[0] or col == column:
            continue
        rows.append(row)
        cols.append(col)
    # look at above row
    if row != grid.shape[0] - 1:
        for col in range(column - 1, column + 2):
            if col < 0 or col >= grid.shape[0]:
                continue
            rows.append(row + 1)
            cols.append(col)

    integer = np.random.randint(len(rows))
    return (rows[integer], cols[integer])


def covid_update_grid(frameNum, img, grid, dim, p, q, r):
    """
    update the graph based off of these rules:

    p = probability of spreading
    q = probability of becoming immune
    r = probability of a move

    states are:
    NON_INFECTED
    INFECTED
    CURED


    """

    newGrid = grid.copy()

    for row in range(dim):
        for col in range(dim):
            if grid[row, col] == NON_INFECTED:
                # can only get infected
                num_infected_neighbors = covid_count_infected_neighbors(row, col, grid)
                if p * num_infected_neighbors >= 1:
                    newGrid[row, col] = INFECTED
                else:
                    newGrid[row, col] = np.random.choice([INFECTED, NON_INFECTED], p=[p * num_infected_neighbors,
                                                                                      1 - (p * num_infected_neighbors)])

            elif grid[row, col] == INFECTED:
                # can only get cured
                newGrid[row, col] = np.random.choice([INFECTED, CURED], p=[1 - q, q])
    for row in range(dim):
        for col in range(dim):
            # make a move proportional to r
            if random.random() < r:
                # select a random neighbor to swap with
                coordinate = covid_get_swappable(row, col, grid)
                to_swap_row = list(coordinate)[0]
                to_swap_col = list(coordinate)[1]
                newGrid[to_swap_row, to_swap_col], newGrid[row, col] = newGrid[row, col], newGrid[
                    to_swap_row, to_swap_col]

    img.set_data(newGrid)
    grid[:] = newGrid[:]


def covid_run_simulation(grid_size=100, p_non_infected=.10, p_infected=.01, updateInterval=500, seed=42, p=.9, q=.1,
                         r=.33):
    """ Function to run the full simulation
    Each frame is an iteration of the model which calls update_grid
    with the arguments listed in fargs

    img should be updated with img.set_data(newGrid) in each iteration of update_grid

    """
    # declare grid
    grid = np.array([])
    grid = covid_random_grid(grid_size, p_non_infected, p_infected, seed=seed)

    # set up animation
    fig, ax = plt.subplots(figsize=(6, 6))
    img = ax.imshow(grid)
    anim = animation.FuncAnimation(fig, covid_update_grid, fargs=(img, grid, grid_size, p, q, r),
                                   frames=100,
                                   interval=updateInterval)

    #anim.save('gol.gif', writer='imagemagick', fps=60)
    return HTML(anim.to_html5_video())

# PySimpleGUI interface
'''
layout = [[sg.Text("Fill out variables below to generate animated simulation")],
          [sg.Text("Simulation will play 5 times")],
          [sg.Text("What is p? (chance of spreading infection, try .9)")],
          [sg.Input(key='-P-')],
          [sg.Text("What is q? (chance of active infection ending, try .1)")],
          [sg.Input(key="-Q-")],
          [sg.Text("What is r? (chance of someone moving, try .1)")],
          [sg.Input(key="-R-")],
          [sg.Text("What proportion of squares are infected people? (try .01)")],
          [sg.Input(key="-P_INFECT-")],
          [sg.Text("What proportion of squares are non-infected people? (try .33)")],
          [sg.Input(key="-P_NON_INFECT-")],
          [sg.Text("How big is the grid? (try 100)")],
          [sg.Input(key="-DIM-")],
          [sg.Button('Ok'), sg.Button('Quit')]]

window = sg.Window('COVID Simulator', layout)

while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED or event == 'Quit':
        break
    # do covid simulator here
    game_of_covid = covid_run_simulation(grid_size=int(values["-DIM-"]),
                                         p_non_infected=float(values['-P_NON_INFECT-']),
                                         p_infected=float(values['-P_INFECT-']),
                                         p=float(values['-P-']),
                                         q=float(values['-Q-']),
                                         r=float(values['-R-']))
    os.system("open gol.gif")

window.close()
'''

# flask interface
from flask import Flask, redirect, url_for, render_template, request, Blueprint

covid_simulator = Blueprint('covid_simulator', __name__, template_folder='templates')
@covid_simulator.route("/", methods=['POST', 'GET'])
def covid_home():
    if request.method == "POST":
        p = request.form["p"]
        q = request.form["q"]
        r = request.form["q"]
        infected = request.form["infected"]
        non_infected = request.form["non-infected"]
        grid_size = request.form["grid-size"]
        return redirect(url_for("covid_simulator.covid", p=p, q=q, r=r, infected=infected, non_infected=non_infected, grid_size=grid_size))
    else:
        return render_template("covid.html")

@covid_simulator.route("/<p>/<q>/<r>/<infected>/<non_infected>/<grid_size>")
def covid(p, q, r, infected, non_infected, grid_size):
    game_of_covid = covid_run_simulation(grid_size=int(grid_size),
                                         p_non_infected=float(non_infected),
                                         p_infected=float(infected),
                                         p=float(p),
                                         q=float(q),
                                         r=float(r))
    return game_of_covid.data
