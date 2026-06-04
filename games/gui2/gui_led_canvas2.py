# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: gui2\gui_led_canvas2.py
import decimal, math
from tkinter import *
from model.setting import Color, Setting

class CanvasLed:
    BORDER_COLR = (177, 177, 177)

    def __init__(self, root, led_row, led_col, side=None, type=1):
        if side is None:
            side_ = 15
        else:
            side_ = side
        width = led_col * side_
        high = led_row * side_
        border = 1
        self.side = side_
        self.width = width
        self.high = high
        self.border = border
        self.row = led_row
        self.col = led_col
        size = (
         width + border * led_col + border, high + border * led_row + border)
        self.size = size
        canvas = Canvas(root, width=(size[0]), height=(size[1]), bg="#ababab")
        canvas.pack(side=TOP)
        self.canvas = canvas
        self.arr2 = self.gen_rectangle_arr(type=type)
        self.arr_canvas_text = []

    def screen_coord_to_led_coord(self, pos_tuple):
        cell_width = self.width / self.col
        cell_height = self.high / self.row
        left = pos_tuple[0]
        top = pos_tuple[1]
        col = (left - self.border) / (cell_width + self.border)
        row = (top - self.border) / (cell_height + self.border)
        row = math.floor(row)
        col = math.floor(col)
        if row < 0:
            row = 0
        if row >= self.row:
            row = self.row - 1
        if col < 0:
            col = 0
        if col >= self.col:
            col = self.col - 1
        pos = (
         row, col)
        return pos

    def led_coord_to_screen_coord(self, pos_tuple):
        row_screen_pos = int(pos_tuple[0] * (self.side + self.border))
        col_screen_pos = int(pos_tuple[1] * (self.side + self.border))
        return (row_screen_pos, col_screen_pos)

    def draw_hexagon3(self, canvas, center_x, center_y, size, fill='gray', outline='gray'):
        size = size / 2
        points = [
         (
          center_x, center_y - size),
         (
          center_x + size * 0.866, center_y - 0.5 * size),
         (
          center_x + size * 0.866, center_y + 0.5 * size),
         (
          center_x, center_y + size),
         (
          center_x - size * 0.866, center_y + 0.5 * size),
         (
          center_x - size * 0.866, center_y - 0.5 * size)]
        size = size * 2 / 3
        points2 = [
         (
          center_x, center_y - size),
         (
          center_x + size * 0.866, center_y - 0.5 * size),
         (
          center_x + size * 0.866, center_y + 0.5 * size),
         (
          center_x, center_y + size),
         (
          center_x - size * 0.866, center_y + 0.5 * size),
         (
          center_x - size * 0.866, center_y - 0.5 * size)]
        size = size * 1 / 2
        points3 = [
         (
          center_x, center_y - size),
         (
          center_x + size * 0.866, center_y - 0.5 * size),
         (
          center_x + size * 0.866, center_y + 0.5 * size),
         (
          center_x, center_y + size),
         (
          center_x - size * 0.866, center_y + 0.5 * size),
         (
          center_x - size * 0.866, center_y - 0.5 * size)]
        polygon1 = canvas.create_polygon(points, fill=fill, outline="black")
        polygon2 = canvas.create_polygon(points2, fill=fill, outline="black")
        polygon3 = canvas.create_polygon(points3, fill=fill, outline="black")
        return (
         polygon1, polygon2, polygon3)

    def draw_hexagon1(self, canvas, center_x, center_y, size, fill='gray', outline='gray'):
        size = size / 2
        points = [
         (
          center_x, center_y - size),
         (
          center_x + size * 0.866, center_y - 0.5 * size),
         (
          center_x + size * 0.866, center_y + 0.5 * size),
         (
          center_x, center_y + size),
         (
          center_x - size * 0.866, center_y + 0.5 * size),
         (
          center_x - size * 0.866, center_y - 0.5 * size)]
        polygon = canvas.create_polygon(points, fill=fill, outline="black")
        return polygon

    def gen_rectangle_arr(self, type=1):
        canvas = self.canvas
        if canvas is not None:
            color = CanvasLed.BORDER_COLR
            cell_width = self.width / self.col
            cell_height = self.high / self.row
            arr2 = [[None] * self.col for _ in range(self.row)]
            color_ = "#" + "{:02X}".format(color[0]) + "{:02X}".format(color[1]) + "{:02X}".format(color[2])
            if type == 1:
                for row in range(self.row):
                    for col in range(self.col):
                        left = col * (cell_width + self.border) + self.border
                        top = row * (cell_height + self.border) + self.border
                        if row == 0:
                            top = 3
                        if col == 0:
                            left = 3
                        arr2[row][col] = self.draw_hexagon3(canvas, (left + cell_width / 2), (top + cell_height / 2), cell_width, fill=color_, outline=color_)

            else:
                for row in range(self.row):
                    for col in range(self.col):
                        left = col * (cell_width + self.border) + self.border
                        top = row * (cell_height + self.border) + self.border
                        if row == 0:
                            top = 3
                        if col == 0:
                            left = 3
                        arr2[row][col] = self.draw_hexagon1(canvas, (left + cell_width / 2), (top + cell_height / 2), cell_width, fill=color_,
                          outline=color_)

        else:
            arr2 = None
        return arr2

    def gen_canvas_text_arr(self):
        canvas = self.canvas
        if canvas is not None:
            color = CanvasLed.BORDER_COLR
            cell_width = self.width / self.col
            cell_height = self.high / self.row
            arr2 = [[None] * self.col for _ in range(self.row)]
            for row in range(self.row):
                for col in range(self.col):
                    left = col * (cell_width + self.border) + self.border
                    top = row * (cell_height + self.border) + self.border
                    if row == 0:
                        top = 3
                    if col == 0:
                        left = 3
                    color_ = "#" + "{:02X}".format(color[0]) + "{:02X}".format(color[1]) + "{:02X}".format(color[2])
                    arr2[row][col] = canvas.create_text(((2.0 * left + cell_width) / 2.0), ((2 * top + cell_height) / 2), text="")

        else:
            arr2 = None
        return arr2

    def write_serial_num_in_rectangle(self, direct=0, start=0):
        canvas = self.canvas
        if canvas is not None:
            color = CanvasLed.BORDER_COLR
            cell_width = self.width / self.col
            cell_height = self.high / self.row
            for row in range(self.row):
                for col in range(self.col):
                    left = col * (cell_width + self.border) + self.border
                    top = row * (cell_height + self.border) + self.border
                    if row == 0:
                        top = 3
                    elif col == 0:
                        left = 3
                    if direct == 0:
                        text = "{:02d}".format(col + start)
                    else:
                        text = "{:02d}".format(row + start)
                    canvas.create_text(((2.0 * left + cell_width) / 2.0), ((2 * top + cell_height) / 2), text=text)

    def create_canvas_text_arr(self):
        self.arr_canvas_text = self.gen_canvas_text_arr()
        return

    def write_text_in_table(self, coors, text=''):
        canvas = self.canvas
        canvas.itemconfig((self.arr_canvas_text[coors[0]][coors[1]]), text=text, font=('Purisa',
                                                                                       8))

    def write_text_by_table(self, table):
        canvas = self.canvas
        for i in range(len(table)):
            for j in range(len(table[0])):
                canvas.itemconfig((self.arr_canvas_text[i][j]), text=(str(table[i][j])), font=('Purisa',
                                                                                               8))

    def write_rect_color_in_table(self, coors, color=Color.WHITE_FORMAT):
        canvas = self.canvas
        if canvas is not None:
            cell_width = self.width / self.col
            cell_height = self.high / self.row
            row = coors[0]
            col = coors[1]
            left = col * (cell_width + self.border) + self.border
            top = row * (cell_height + self.border) + self.border
            if row == 0:
                top = 3
            if col == 0:
                left = 3
            canvas.create_rectangle(left, top, (left + int(cell_width)), (top + int(cell_height)), fill=color)

    def draw_led_color(self, logic_2array):
        led_canvas = self.canvas
        if led_canvas is not None:
            for i in range(len(logic_2array)):
                for j in range(len(logic_2array[i])):
                    for k in range(3):
                        color = logic_2array[i][j][k]
                        color_ = "#" + "{:02X}".format(color[0]) + "{:02X}".format(color[1]) + "{:02X}".format(color[2])
                        led_canvas.itemconfig((self.arr2[i][j][k]), fill=color_, outline="black")

    def draw_led_color_type_0(self, logic_2array):
        led_canvas = self.canvas
        if led_canvas is not None:
            for i in range(len(logic_2array)):
                for j in range(len(logic_2array[i])):
                    color = logic_2array[i][j]
                    color_ = "#" + "{:02X}".format(color[0]) + "{:02X}".format(color[1]) + "{:02X}".format(color[2])
                    led_canvas.itemconfig((self.arr2[i][j]), fill=color_, outline="black")

    def draw_led_table_color(self, led_table):
        led_canvas = self.canvas
        arr2 = self.arr2
        len_row = len(led_table)
        len_col = len(led_table[0])
        if led_canvas is not None:
            for i in range(len_row):
                for j in range(len_col):
                    led_canvas.itemconfig((arr2[i][j]), fill=(led_table[i][j]), outline="gray")

    def draw_line_in_table(self, col, line_type='col'):
        screen_coord_start = self.led_coord_to_screen_coord((0, col))
        screen_coord_end = self.led_coord_to_screen_coord((self.high, col))
        self.canvas.create_line((screen_coord_start[1]), 0, (screen_coord_start[1]), (screen_coord_end[0]), fill="yellow")

    def clear_table_color(self, table, type=1):
        led_canvas = self.canvas
        if led_canvas is not None:
            if type == 1:
                for i in range(len(table)):
                    for j in range(len(table[i])):
                        if table[i][j]:
                            for k in range(3):
                                led_canvas.itemconfig((self.arr2[i][j][k]), fill=(Color.WHITE_FORMAT))

                            table[i][j] = False

            else:
                for i in range(len(table)):
                    for j in range(len(table[i])):
                        if table[i][j]:
                            led_canvas.itemconfig((self.arr2[i][j]), fill=(Color.WHITE_FORMAT))
                            table[i][j] = False

    def set_table_specified_color(self, range_in_ij, color=[
 Color.WHITE_FORMAT] * 3):
        for i in range(range_in_ij[0][0], range_in_ij[0][1] + 1):
            for j in range(range_in_ij[1][0], range_in_ij[1][1] + 1):
                for k in range(3):
                    self.canvas.itemconfig((self.arr2[i][j][k]), fill=(color[k]))

    def set_table_specified_color_0(self, range_in_ij, color=Color.WHITE_FORMAT):
        for i in range(range_in_ij[0][0], range_in_ij[0][1] + 1):
            for j in range(range_in_ij[1][0], range_in_ij[1][1] + 1):
                self.canvas.itemconfig((self.arr2[i][j]), fill=color)

    def draw_state_table(self, table, color=Color.WHITE_FORMAT):
        for i in range(len(table)):
            for j in range(len(table[i])):
                if table[i][j]:
                    self.canvas.itemconfig((self.arr2[i][j]), fill=color)

    def draw_set_cell(self, set_cell, color=Color.WHITE):
        color = "#" + "{:02X}".format(color[0]) + "{:02X}".format(color[1]) + "{:02X}".format(color[2])
        for coor in set_cell:
            i = round(coor[0])
            j = round(coor[1])
            self.canvas.itemconfig((self.arr2[i][j]), fill=color)

    def draw_table_cell(self, cell, color3=[Color.WHITE] * 3):
        i = round(cell[0])
        j = round(cell[1])
        for k in range(3):
            color = color3[k]
            color = "#" + "{:02X}".format(color[0]) + "{:02X}".format(color[1]) + "{:02X}".format(color[2])
            self.canvas.itemconfig((self.arr2[i][j][k]), fill=color)

    def draw_table_cell_0(self, cell, color=Color.WHITE):
        i = round(cell[0])
        j = round(cell[1])
        color = "#" + "{:02X}".format(color[0]) + "{:02X}".format(color[1]) + "{:02X}".format(color[2])
        self.canvas.itemconfig((self.arr2[i][j]), fill=color)

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/gui2/gui_led_canvas2.pyc
