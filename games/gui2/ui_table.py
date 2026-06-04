# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: gui2\ui_table.py
import tkinter
from tkinter import Frame, RIGHT, Y, BOTTOM, X, ttk, NO, CENTER
from tkinter.ttk import Scrollbar, Treeview

class Table:

    def clear(self):
        x = self.my_game.get_children()
        for item in x:
            self.my_game.delete(item)

    def reflesh_data(self, col_title=[], data=[]):
        self.clear()
        self.refresh_col_title(col_title)
        row_id = 0
        for val in data:
            self.my_game.insert(parent="", index="end", iid=row_id, text="", values=val)
            row_id += 1

    def refresh_col_title(self, col_title=[]):
        self.my_game["columns"] = col_title
        self.my_game.column("#0", width=0, stretch=NO)
        self.my_game.heading("#0", text="", anchor=CENTER)
        for col in col_title:
            self.my_game.column(col, anchor=CENTER, width=120, minwidth=50)
            self.my_game.heading(col, text=col, anchor=CENTER)

    def __init__(self, root, col_title=[], data=[]):
        game_frame = Frame(root, width=800)
        game_frame.pack()
        self.col_title = col_title
        game_scroll_ver = Scrollbar(game_frame, orient="vertical")
        game_scroll_ver.pack(side=RIGHT, fill=Y)
        game_scroll = Scrollbar(game_frame, orient="horizontal")
        game_scroll.pack(side=BOTTOM, fill=X)
        my_game = Treeview(game_frame, yscrollcommand=(game_scroll_ver.set), xscrollcommand=(game_scroll.set))
        my_game.pack()
        self.my_game = my_game
        game_scroll_ver.config(command=(my_game.yview))
        game_scroll.config(command=(my_game.xview))
        my_game["columns"] = col_title
        my_game.column("#0", width=0, stretch=NO)
        my_game.heading("#0", text="", anchor=CENTER)
        for col in col_title:
            my_game.column(col, anchor=CENTER, width=120, minwidth=50)
            my_game.heading(col, text=col, anchor=CENTER)

        row_id = 0
        for val in data:
            my_game.insert(parent="", index="end", iid=row_id, text="", values=val)
            row_id += 1

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/PYZ-00.pyz_extracted/gui2/ui_table.pyc
