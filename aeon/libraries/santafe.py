import random

from .annotation import aefunction, aedocumentation
from aeon.libraries.list import *
from aeon.libraries.pair import *

''' Santa fe trail native binds in Aeon to Python '''
size = 10


@aefunction(f"""type RestrictedNat as {{x:Integer | x == 0 || x == 1}}""", None)
class BoundedInt(object):
    def __init__(self):
        pass

@aefunction(f"""type BoundedInt as {{x:Integer | x >= 0 && x <= {size}}}""", None)
class BoundedInt(object):
    def __init__(self):
        pass

@aefunction(f"""type Grid {{
    grid : List[List[RestrictedNat]];
    food : {{food:Integer | food >= 0}};
    position : Pair[BoundedInt, BoundedInt];
}}""", None)
class Grid(object):
    def __init__(self, grid, food, position):
        self.grid = grid
        self.food = food
        self.position = position
        
# Create grid
@aefunction('create_grid({food:Integer | food >= 0}) -> {g:Grid | g.food == (food - 1)} = native;', lambda food: create_grid(food))
def create_grid(food):
    position = create_pair(0, 0)
    grid = random_grid(food, 10, 10)
    return Grid(grid, food, position)


# Ugly code
def random_grid(food, size_x, size_y):
    def move_x(x):
        options = list()
        if x - 1 >= 0:
            options.append(x - 1)
        if x + 1 < size_x:
            options.append(x + 1)
        return random.choice(options)
    def move_y(y):
        options = list()
        if y - 1 >= 0:
            options.append(y - 1)
        if y + 1 < size_y:
            options.append(y + 1)
        return random.choice(options)
    def has_food_around(x, y, result):
        out = False
        if x - 1 >= 0:
            out = out or result[y][x - 1]
        if x + 1 < size_x:
            out = out or result[y][x + 1]
        if y - 1 >= 0:
            out = out or result[y - 1][x]  
        if y + 1 < size_y:
            out = out or result[y + 1][x]
        return out    

    result = [[0 for col in range(size_x)] for row in range(size_y)]
    x, y = 0, 0

    result[y][x] = 1
    food -= 1

    if random.random() < 0.5:
        new_x = move_x(x)
        new_y = y
    else:
        new_x = x
        new_y = move_y(y)

    prev_move = (new_x - x, new_y - y)
    x, y = new_x, new_y

    while food > 0:
            
        if random.random() < 0.25 or (prev_move[0] + x >= size_x or \
                                     prev_move[0] + x < 0 or \
                                     prev_move[1] + y >= size_y or \
                                     prev_move[1] + y < 0):
            if random.random() < 0.5:
                new_x = move_x(x)
                new_y = y
            else:
                new_x = x
                new_y = move_y(y)
        else:
            new_x, new_y = prev_move[0] + x, prev_move[1] + y

        if not result[y][x]:
            if not has_food_around(x, y, result) and ((new_x - x, new_y - y) == prev_move):
                result[y][x] = 1
                food -= 1
            else:
                if random.random() < 0.5:
                    result[y][x] = 1
                    food -= 1
        
        prev_move = (new_x - x, new_y - y)
        x, y = new_x, new_y
    
    return result

def inside_limites(value, minimum, maximum):
    return value >= minimum and value < maximum


@aefunction('food_present(g:Grid) -> {out:Integer | i >= 0 && i <= g.food} = native;', lambda grid: food_present(grid))
def food_present(grid):
    grid = grid.copy()
    return grid.grid[grid.position[1]][grid.position[0]]

@aefunction('left({g:Grid | g.position.elem1 > 0}) -> {g2:Grid | g2.position.elem1 == (g.position.elem1 - 1)} = native;', lambda grid: left(grid))
def left(grid):
    grid = grid.copy()
    grid.position = (grid.position[0] - 1, grid.position[1])
    if grid.grid[grid.position[1]][grid.position[0]]:
        grid.food -= 1
        grid.grid[grid.position[1]][grid.position[0]] = 0
    return grid

@aefunction('right({g:Grid | g.position.elem1 < g.grid.size}) -> {g2:Grid | g2.position.elem1 == (g.position.elem1 + 1)} = native;', lambda grid: right(grid))
def right(grid):
    grid = grid.copy()
    grid.position = (grid.position[0] + 1, grid.position[1])
    if grid.grid[grid.position[1]][grid.position[0]]:
        grid.food -= 1
        grid.grid[grid.position[1]][grid.position[0]] = 0
    return grid

@aefunction('up({g:Grid | g.position.elem2 > 0}) -> {g2:Grid | g2.position.elem2 == (g.position.elem2 - 1)} = native;', lambda grid: up(grid))
def up(grid):
    grid = grid.copy()
    grid.position = (grid.position[0], grid.position[1] - 1)
    if grid.grid[grid.position[1]][grid.position[0]]:
        grid.food -= 1
        grid.grid[grid.position[1]][grid.position[0]] = 0
    return grid

@aefunction('down({g:Grid | g.position.elem2 < g.grid.size}) -> {g2:Grid | g2.position.elem2 == (g.position.elem2 + 1)} = native;', lambda grid: down(grid))
def down(grid):
    grid = grid.copy()
    grid.position = (grid.position[0], grid.position[1] + 1)
    if grid.grid[grid.position[1]][grid.position[0]]:
        grid.food -= 1
        grid.grid[grid.position[1]][grid.position[0]] = 0
    return grid

@aefunction('get_grid(g:Grid) -> List[List[RestrictedNat]] = native;', lambda grid: get_grid(grid))
def get_grid(grid):
    return grid.grid

@aefunction('get_food(g:Grid) -> Integer = native;', lambda grid: get_food(grid))
def get_food(grid):
    return grid.food

@aefunction('get_position(g:Grid) -> Pair[BoundedInt, BoundedInt] = native;', lambda grid: get_position(grid))
def get_position(grid):
    return grid.position

@aefunction('set_grid(l:List[List[RestrictedNat]], g:Grid) -> Grid = native;', lambda l: lambda grid: set_grid(l, grid))
def set_grid(l, grid):
    grid = grid.copy()
    grid.grid = l
    return grid

@aefunction('set_position(pos:Pair[BoundedInt, BoundedInt], g:Grid) -> Grid = native;', lambda pos: lambda grid: set_position(pos, grid))
def set_position(pos, grid):
    grid = grid.copy()
    grid.pos = pos
    return grid

@aefunction('consume_food(g:Grid, x:BoundedInt, y:BoundedInt) -> {g2:Grid | g.food - 1 == g2.food} = native;', lambda grid: lambda x: lambda y: consume_food(grid, x, y))
def consume_food(grid, x, y):
    grid = grid.copy()
    grid.food -= 1
    grid.grid[y][x] = 0
    return grid