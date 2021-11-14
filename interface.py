import tkinter as tk
import tkinter.messagebox as msg
import pathlib
from pathlib import Path
from tkinter import ttk
from tkinter import *

from database import JsonDatabase
from table import JsonManager

LARGEFONT = ("Verdana", 14)
CURRENT_DB = None


def insert_workdir(entry: Entry):
    cwd = pathlib.Path(__file__).parent.resolve()
    entry.insert(0, cwd)


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
        label = ttk.Label(self, text=f"Database: {db_name}", font=LARGEFONT)
        label.grid(row=0, column=4, padx=10, pady=10)

        # commands executing interface
        entry_cmd = ttk.Entry(self)
        entry_cmd.grid(row=1, column=1, padx=10, pady=10)
        exec_button = ttk.Button(self, text="Execute",
                                 command=lambda: self._execute(entry_cmd.get()))
        exec_button.grid(row=1, column=2, padx=10, pady=10)

        # table open & create
        entry_table = ttk.Entry(self)
        entry_table.grid(row=2, column=1, padx=10, pady=10)
        table_button = ttk.Button(self, text="Open / Create Table",
                                  command=lambda: self._execute(None))
        table_button.grid(row=2, column=2, padx=10, pady=10)

        # column addition interface
        entry_column_name = ttk.Entry(self)
        entry_column_name.grid(row=3, column=1, padx=10, pady=10)
        is_column_required = tk.BooleanVar()
        is_column_primary = tk.BooleanVar()
        required_column_box = ttk.Checkbutton(self, text="Required", variable=is_column_required,
                                              onvalue=True, offvalue=False)
        required_column_box.grid(row=3, column=2, padx=10, pady=10)
        primary_column_box = ttk.Checkbutton(self, text="Primary", variable=is_column_primary,
                                             onvalue=True, offvalue=False)
        primary_column_box.grid(row=3, column=3, padx=10, pady=10)
        add_column_button = ttk.Button(self, text="Add column",
                                       command=lambda: self._add_column(entry_column_name.get(),
                                                                        is_column_required.get(),
                                                                        is_column_primary.get()))
        add_column_button.grid(row=3, column=4, padx=10, pady=10)

        # add record -> column_name:value:type,column_name:value:type,column_name:value:type
        entry_record = ttk.Entry(self)
        entry_record.grid(row=4, column=1, padx=10, pady=10)
        add_record_button = ttk.Button(self, text="Add record",
                                       command=lambda: self._add_record(entry_record.get()))
        add_record_button.grid(row=4, column=2, padx=10, pady=10)

    def _execute(self, cmd):
        #
        pass

    def _add_column(self, name, is_required, is_primary):
        pass

    def _add_record(self, params):
        pass


app = App()
app.title("Json Database v1.0")
app.geometry("640x480")
app.mainloop()
