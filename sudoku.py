#!/usr/bin/env python3
import collections
import dataclasses
import fileinput
import itertools
import pprint
import sys
import unicodedata

class NestedBreak(Exception):
    """For breaking out of nested loops."""
    pass

THREE = 3
NINE = 9
CR = "\n"
SPACE = " "
DASH = "-"
ALL_NINE = set([str(x) for x in range(1, NINE + 1)])
LIGHT_DASH = unicodedata.lookup("BOX DRAWINGS LIGHT DOUBLE DASH HORIZONTAL")
HEAVY_DASH = unicodedata.lookup("BOX DRAWINGS HEAVY DOUBLE DASH HORIZONTAL")
LIGHT_VERT = unicodedata.lookup("BOX DRAWINGS LIGHT DOUBLE DASH VERTICAL")
HEAVY_VERT = unicodedata.lookup("BOX DRAWINGS HEAVY DOUBLE DASH VERTICAL")
# A list of the cells going by 3x3 boxes
BOX_LIST = list()
for i in range(0, NINE, THREE):  # 0,3,6
    for j in range(0, NINE, THREE):  # 0,3,6
        row_range = range(i, i + THREE)
        col_range = range(j, j + THREE)
        BOX_LIST.append(list(itertools.product(row_range, col_range)))
# A list of the cells going by rows
ROW_LIST = list()
# A list of the cells going by cols
COL_LIST = list()
for i in range(NINE):
    ROW_LIST.append(list(itertools.product([i], range(NINE))))
    COL_LIST.append(list(itertools.product(range(NINE), [i])))

def get_box_cells(row, col):
    """by box"""
    # Given a row/col, return a list of the cells in the box this cell is in.
    which_row = int(row / THREE)
    which_col = int(col / THREE)
    box_index = THREE * which_row + which_col
    return BOX_LIST[box_index]

def get_row_cells(row, col):
    """by row"""
    # Given a row, return a list of the cells in that row.
    return ROW_LIST[row]

def get_col_cells(row, col):
    """by col"""
    # Given a col, return a list of the cells in that col.
    return COL_LIST[col]

def describe_change(row, col, previous_set, new_set, explanation):
    previous_description = "/".join(sorted(list(previous_set)))
    new_description = "/".join(sorted(list(new_set)))
    if len(new_set) == 1:
        verb = "Solved"
    else:
        verb = "Changed"
    return f"{verb} {row + 1},{col + 1} from {previous_description} to {new_description} ({explanation})."

class board():
    # board_array contains 81 cells,
    # each cell contains a string of characters (numbers) the cell can be
    @staticmethod
    def get_printed_board(array):
        BOARD_WIDTH = 55
        return_string = ""
        return_string += HEAVY_DASH * BOARD_WIDTH + CR
        for row in range(NINE):
            for sub_row in range(THREE):
                return_string += HEAVY_VERT + SPACE
                for col in range(NINE):
                    lower_bound = 1 + THREE * sub_row
                    upper_bound = lower_bound + THREE
                    for to_print in range(lower_bound, upper_bound):
                        char = str(to_print)
                        if char in array[row][col]:
                            return_string += char
                        else:
                            return_string += DASH
                    if (col + 1) % THREE == 0:
                        return_string += SPACE + HEAVY_VERT + SPACE
                    else:
                        return_string += SPACE + LIGHT_VERT + SPACE
                return_string += CR
            if (row + 1) % THREE == 0:
                return_string += HEAVY_DASH * BOARD_WIDTH + CR
            else:
                return_string += LIGHT_DASH * BOARD_WIDTH + CR
        return return_string

    def __init__(self, data_list):
        self.board_array = [[ALL_NINE.copy() for x in range(NINE)] for y in range(NINE)]
        for row, line in enumerate(data_list):
            if row >= NINE:
                break
            for col, char in enumerate(line.rstrip()):
                if char != SPACE:
                    self.board_array[row][col] = set(char)

    def __repr__(self):
        return board.get_printed_board(self.board_array)

    def get_single_value(self, row, col):
        # Return a char, or None
        value = self.board_array[row][col]
        if len(value) == 1:
            return list(value)[0]
        return None

    def get_cell(self, row, col):
        return self.board_array[row][col].copy()

    def get_negative_value_set(self, row, col):
        # Return a set of the values this cell could be
        return ALL_NINE - self.board_array[row][col]

    def get_mirror_version(self):
        # Suitable for printing, shows the values the cell _could not_ be
        human = [[None for x in range(NINE)] for y in range(NINE)]
        for row in range(NINE):
            for col in range(NINE):
                human[row][col] = self.get_negative_value_set(row, col)
        return board.get_printed_board(human)

    def set_cell(self, row, col, value):
        if type(value) == type(set()):
            self.board_array[row][col] = value.copy()
        elif type(value) == type(SPACE):
            self.board_array[row][col] = set(str(value))
        else:
            raise

    def is_cell_legal(self, row, col, value):
        """Would it be legal to put this value in this cell?"""
        value = str(value)
        for r, c in get_box_cells(row, col):
            if self.board_array[r][c] == [value]:
                return False
        for r, c in ROW_LIST[row]:
            if self.board_array[r][c] == [value]:
                return False
        for r, c in COL_LIST[col]:
            if self.board_array[r][c] == [value]:
                return False
        return True

    def is_cell_solved(self, row, col):
        return len(self.get_cell(row, col)) == 1

    def is_section_solved(self, cell_list):
        """Verify that each of the nine values '1' through '9' are present"""
        my_set = ALL_NINE.copy()
        for row, col in cell_list:
            value = self.get_cell(row, col)
            if len(value) == 1:
                my_set.discard(value.pop())
            else:
                return False
        if my_set:
            return False
        return True

    def is_solved(self):
        for box in BOX_LIST:
            if not self.is_section_solved(box):
                return False
        for row in ROW_LIST:
            if not self.is_section_solved(row):
                return False
        for col in COL_LIST:
            if not self.is_section_solved(col):
                return False
        return True

    def get_existing_values(self, cell_list):
        """Return a set of definitive values."""
        values = set([self.get_single_value(rr, cc) for rr, cc in cell_list])
        values.discard(None)
        return values

    def get_multiples(self, cells_to_survey, count):
        """Suppose a box (or row, or columns) contains:
        {}, {'1'}, {'7'}, {'2'}, {}, {}, {'3', '4'}, {'3', '4'}, {'8'}
        In this case, the unknown cell numbers 0, 4 and 5 cannot be a '3' or '4',
        because cell number 6 must be a '3' or '4' and cell number 7 must be a '3' or '4'
        and the box (or row, or columns) can contain only one '3' and one '4'.
        Likewise for triples, quadruples, etc. For example, Suppose a box (or row, or columns) contains:
        {}, {'1', '3', '4'}, {'7'}, {'2'}, {}, {}, {'1', '3'}, {'3', '4'}, {'8'}.
        In this case, the unknown cell numbers 0, 4 and 5 cannot be a '1', '3' or '4'.
        Returns a tuple containing two sets.
        The first set contains the cells containing these multiples,
        and the second set contains the values in these cells.
        """
        for combination in itertools.combinations(cells_to_survey, count):
            # print(" & ".join([str(x) for x in cells_to_survey]))
            unique_value_set = set()
            is_candidate = True
            for row, col in combination:
                if len(self.get_cell(row, col)) == 1:
                    is_candidate = False
                    break
                unique_value_set.update(self.get_cell(row, col))
            if is_candidate and len(unique_value_set) == count:
                return (set(combination[:]), unique_value_set)
        return (set(), set())

def solve(a_board):
    """Return True if solved."""
    is_changed = True
    while is_changed:
        if a_board.is_solved():
            return True
        print(a_board)
        is_changed = False
        for row in range(NINE):
            for col in range(NINE):
                # Only concern ourselves with cells that are not solved
                if not a_board.get_single_value(row, col):
                    # print(f"Working on {row+1}, {col+1} ...")
                    # Start with the current potential values
                    original_set = a_board.get_cell(row, col)
                    candidate_set = original_set.copy()
                    # Now remove the values this cell could not be
                    candidate_set -= a_board.get_existing_values(get_box_cells(row, col))
                    candidate_set -= a_board.get_existing_values(get_row_cells(row, col))
                    candidate_set -= a_board.get_existing_values(get_col_cells(row, col))
                    # Set and report (if needed)
                    if original_set != candidate_set:
                        a_board.set_cell(row, col, candidate_set.copy())
                        is_changed = True
                        print(describe_change(row, col, original_set, candidate_set, "by elimination"))
                    # Now remove doubles, triples, etc from that same box
                    for cell_id_method in get_box_cells, get_row_cells, get_col_cells:
                        for count in (2, 3, 4):
                            cell_set, found_value_set = a_board.get_multiples(cell_id_method(row, col), count)
                            if cell_set:
                                for rr, cc in cell_id_method(row, col):
                                    if a_board.is_cell_solved(rr, cc) or (rr, cc) in cell_set:
                                        continue
                                    original_set = a_board.get_cell(rr, cc)
                                    candidate_set = original_set.copy()
                                    for value in found_value_set:
                                        candidate_set.discard(value)
                                    # Set and report (if needed)
                                    if original_set != candidate_set:
                                        a_board.set_cell(rr, cc, candidate_set)
                                        is_changed = True
                                        print(describe_change(rr, cc, original_set, candidate_set, f"{cell_id_method.__doc__} multiple of {count}"))
                '''
                for value in range(1, 1 + NINE):
                    value = str(value)
                    for box_index in range(NINE):
                        possible_cell_set = set()
                        try:
                            for row, col in BOX_LIST[box_index]:
                                if not a_board.get_single_value(row, col) and a_board.is_cell_legal(row, col, value):
                                    possible_cell_set.add((row, col))
                                    if len(possible_cell_set) > 1:
                                        raise NestedBreak
                            if possible_cell_set:
                                row, col = possible_cell_set.pop()
                                a_board.set_cell(row, col, value)
                                print(f"Set ({row + 1},{col + 1}) to '{value}'.")
                                is_changed = True
                        except NestedBreak:
                            pass
                '''
        # X-wing
        continue
        tracker = dict()
        for row in range(NINE):
            for col in range(NINE):
                for value in a_board.get_cell(row, col):
                    if not tracker[value]:
                        tracker[value] = (list(), list())

            pass
    return False

my_board = board(fileinput.input())
print("Starting with:" + CR + str(my_board))
# sys.exit()
is_solved = solve(my_board)
print(my_board)
if is_solved:
    print("Solved!")
