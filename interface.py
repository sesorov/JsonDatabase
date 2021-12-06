import os
import tkinter as tk
import tkinter.messagebox as msg
import pathlib

import tabulate

from pathlib import Path
from tkinter import ttk
from tkinter import *
from subprocess import Popen, PIPE

from database import JsonDatabase
from table import JsonManager

LARGEFONT = ("Verdana", 14)
CURRENT_DB = None
CURRENT_TABLE = None

script_path = os.path.join(Path(__file__).parent, 'main.py')


def insert_workdir(entry: Entry):
    cwd = pathlib.Path(__file__).parent.resolve()
    entry.insert(0, cwd)


def db_execute(cmd_raw):
    cmd = ' '.join([sys.executable, script_path]) + ' ' + cmd_raw
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, encoding='utf-8')
    err = p.stderr.readline()
    out = p.stdout.readline()
    if err:
        raise RuntimeError(err)
    return out


class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, CreatePage, OpenPage, OperationsPage):
            frame = F(container, self)
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        try:
            frame.update()
        except Exception as e:
            pass  # TODO: add logger
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = ttk.Label(self, text="JsonDB v1.0", font=LARGEFONT)
        label.grid(row=0, column=4, padx=10, pady=10)
        labels = {'File': self.get_file_menu(), 'Help': self.get_help_menu()}
        main_menu = Menu()
        for label, menu in labels.items():
            main_menu.add_cascade(label=label, menu=menu)
        controller.config(menu=main_menu)

    def get_file_menu(self):
        file_menu = Menu()

        file_menu.add_command(label="Create", command=lambda: self.controller.show_frame(CreatePage))
        file_menu.add_command(label="Open", command=lambda: self.controller.show_frame(OpenPage))
        file_menu.add_command(label="Backup", command=None)
        file_menu.add_separator()
        file_menu.add_command(label="Exit")

        return file_menu

    def get_help_menu(self):
        help_menu = Menu()

        help_menu.add_command(label="Creating DB", command=None)
        help_menu.add_command(label="Operations", command=None)

        return help_menu


class CreatePage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = ttk.Label(self, text="Create DB in path:", font=LARGEFONT)
        label.grid(row=0, column=4, padx=10, pady=10)

        entry_path = ttk.Entry(self)
        entry_path.grid(row=1, column=4, padx=10, pady=10)

        create_button = ttk.Button(self, text="Create",
                                   command=lambda: self._create(entry_path.get()))
        create_button.grid(row=2, column=1, padx=10, pady=10)

        insert_button = ttk.Button(self, text="Insert current workdir",
                                   command=lambda: insert_workdir(entry_path))
        insert_button.grid(row=3, column=1, padx=10, pady=10)

        open_button = ttk.Button(self, text="Open existing DB",
                                 command=lambda: controller.show_frame(OpenPage))
        open_button.grid(row=4, column=1, padx=10, pady=10)

    def _create(self, path):
        global CURRENT_DB
        msg.showinfo(message=f"Successfully created database {path}")
        file = JsonManager(Path(path))
        CURRENT_DB = JsonDatabase(file)
        self.controller.show_frame(OperationsPage)


class OpenPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = ttk.Label(self, text="Open database from file:", font=LARGEFONT)
        label.grid(row=0, column=4, padx=10, pady=10)

        entry_path = ttk.Entry(self)
        entry_path.grid(row=1, column=4, padx=10, pady=10)

        open_button = ttk.Button(self, text="Open",
                                 command=lambda: self._open(entry_path.get()))
        open_button.grid(row=2, column=1, padx=10, pady=10)

        insert_button = ttk.Button(self, text="Insert current workdir",
                                   command=lambda: insert_workdir(entry_path))
        insert_button.grid(row=3, column=1, padx=10, pady=10)

    def _open(self, path):
        global CURRENT_DB
        file = JsonManager(Path(path))
        CURRENT_DB = JsonDatabase(file)
        self.controller.show_frame(OperationsPage)


class OperationsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

    def update(self):
        global CURRENT_DB
        db_name = CURRENT_DB.file_manager.file.stem
        label_text = StringVar(value=f"Database: {db_name}")
        label = ttk.Label(self, textvariable=label_text, font=LARGEFONT)
        label.grid(row=0, column=4, padx=10, pady=10)

        # commands executing interface
        entry_cmd = ttk.Entry(self)
        entry_cmd.grid(row=1, column=1, padx=10, pady=10)
        exec_button = ttk.Button(self, text="Execute",
                                 command=lambda: db_execute(entry_cmd.get()))
        exec_button.grid(row=1, column=2, padx=10, pady=10)

        # table open & create
        entry_table = ttk.Entry(self)
        entry_table.grid(row=2, column=1, padx=10, pady=10)
        table_button = ttk.Button(self, text="Open / Create Table",
                                  command=lambda: self._table(db_name, entry_table.get(), label_text))
        table_button.grid(row=2, column=2, padx=10, pady=10)

        # column addition interface
        entry_column_name = ttk.Entry(self)
        entry_column_name.grid(row=3, column=1, padx=10, pady=10)
        add_column_button = ttk.Button(self, text="Add primary key",
                                       command=lambda: self._add_key(entry_column_name.get(), CURRENT_TABLE))
        add_column_button.grid(row=3, column=2, padx=10, pady=10)

        # add record -> column_name:value:type column_name:value:type column_name:value:type
        entry_record = ttk.Entry(self, width=50)
        entry_record.grid(row=4, column=1, padx=10, pady=10)
        add_record_button = ttk.Button(self, text="Add record",
                                       command=lambda: self._add_record(entry_record.get(), CURRENT_TABLE))
        add_record_button.grid(row=4, column=2, padx=10, pady=10)

        # delete record(s) by query
        entry_del = ttk.Entry(self, width=50)
        entry_del.grid(row=5, column=1, padx=10, pady=10)
        del_button = ttk.Button(self, text="Delete by query",
                                command=lambda: self._del_record(entry_del.get(), CURRENT_TABLE))
        del_button.grid(row=5, column=2, padx=10, pady=10)

        # view
        entry_view = ttk.Entry(self, width=50)
        entry_view.grid(row=6, column=1, padx=10, pady=10)
        view_button = ttk.Button(self, text="View table (leave field empty for full)",
                                 command=lambda: self._view(entry_view.get()))
        view_button.grid(row=6, column=2, padx=10, pady=10)

    def _table(self, db_name, table_name, label_text=None):
        try:
            global CURRENT_TABLE
            db_execute(f"--path {CURRENT_DB.file_manager.file} set --create --table {table_name}")
            CURRENT_TABLE = table_name
            if label_text:
                label_text.set(f"Database: {db_name}\nTable: {table_name}")
        except RuntimeError as e:
            msg.showerror(message="Error occurred while creating table. Please, check logs."
                                  f"\n[technical]: {str(e)}")

    def _add_key(self, key_name, table_name=CURRENT_TABLE):
        try:
            db_execute(f"--path {CURRENT_DB.file_manager.file} set --table {table_name} --key {key_name}")
            msg.showinfo(message=f"Successfully added primary key {key_name} to {table_name}.")
        except RuntimeError as e:
            msg.showerror(message=f"Couldn't add primary key {key_name} to {table_name}. Please, check logs."
                                  f"\n[technical]: {str(e)}")

    def _add_record(self, params, table_name=CURRENT_TABLE):
        try:
            db_execute(f"--path {CURRENT_DB.file_manager.file} set --table {table_name} "
                       f"--add {params}")
            msg.showinfo(message=f"Successfully added record {params} to {table_name}.")
        except RuntimeError as e:
            msg.showerror(message=f"Couldn't add record {params} to {table_name}. Please, check logs."
                                  f"\n[technical]: {str(e)}")

    def _del_record(self, params, table_name=CURRENT_TABLE):
        try:
            db_execute(f"--path {CURRENT_DB.file_manager.file} set --table {table_name} "
                       f"--delete {params}")
            msg.showinfo(message=f"Successfully added record {params} to {table_name}.")
        except RuntimeError as e:
            msg.showerror(message=f"Couldn't delete anything by {params} in {table_name}. Please, check logs."
                                  f"\n[technical]: {str(e)}")

    def _view(self, query=None):
        import json

        try:
            view_window = Tk()
            view_window.title(f"{CURRENT_DB.file_manager.file}: {CURRENT_TABLE}")

            data = []
            columns = set()
            if query:
                try:
                    data = json.loads(db_execute(f"--path {CURRENT_DB.file_manager.file} get --table {CURRENT_TABLE} "
                                                 f"--search {query}").replace("'", '"'))
                except RuntimeError as e:
                    msg.showerror(message=f"Error occurred while searching {query} in {CURRENT_TABLE}. "
                                          f"Please, check logs."
                                          f"\n[technical]: {str(e)}")
            else:
                data = CURRENT_DB.table(CURRENT_TABLE).get_all()
            for record in data:
                columns.update(list(record.keys()))
            data_tree = ttk.Treeview(view_window, columns=list(columns), show='headings')
            for col in columns:
                data_tree.heading(col, text=col)
            for record in data:
                values = list(record.get(key, '-') for key in columns)
                data_tree.insert("", 'end', values=values)
            data_tree.pack(fill="x")
        except Exception as e:
            msg.showerror(message="Couldn't display any info. Please, check logs."
                                  f"\n[technical] {str(e)}")


app = App()
app.title("Json Database v1.0")
app.geometry("800x480")
app.mainloop()
