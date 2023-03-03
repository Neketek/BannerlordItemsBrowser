from __future__ import annotations
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Iterable, List, Any
from browser.model import Model, Item
from tkinter import filedialog


class ItemsTableFrame(tk.Frame):

    COLUMNS = ("Id", "Name")

    def __init__(self, app: App):
        super().__init__(app.window)
        self.app = app

        self.tree = ttk.Treeview(self, columns=self.COLUMNS, show="headings", selectmode="browse", height=1)
        self.tree.bind("<Double-1>", self.on_select)
        for id in self.COLUMNS:
            self.tree.column(id, width=1, stretch=True)
            self.tree.heading(id, text=id)

        self.v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        # self.h_scrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.v_scrollbar.set)
        # self.tree.configure(xscrollcommand=self.h_scrollbar.set)

        self.columnconfigure(0, weight=1000)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1000)
        self.rowconfigure(1, weight=1)
        self.v_scrollbar.grid(row=0, column=1, sticky="nse", rowspan=2)
        # self.h_scrollbar.grid(row=1, column=0, sticky="wes", columnspan=2)
        self.tree.grid(row=0, column=0, sticky="nsew", rowspan=2)

    def set_values(self, items: List[Item]):
        for element in self.tree.get_children():
            self.tree.delete(element)
        for item in items:
            self.tree.insert("", tk.END, values=(item.id, item.name))

    def on_select(self, event: tk.Event):
        for item in self.tree.selection():
            id, name = self.tree.item(item)["values"]
            self.app.window.clipboard_clear()
            self.clipboard_append(id)
            self.app.info_frame.show_info(f"\"{name}\" id copied to clipboard", "green")


class FilterOptionsFrame(tk.Frame):
    def __init__(self, container, name, options, default="All"):
        super().__init__(container)
        self.default = default
        self.value = tk.StringVar()
        self.value.set(default)

        self.label = ttk.Label(self, text=name)
        self.combobox = ttk.Combobox(self, textvariable=self.value)
        self.reset_button = ttk.Button(self, text="X", command=self.reset, width=10)

        self.set_values(options)

        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=1)
        self.label.grid(row=0, column=0, sticky="we", pady=5)
        self.combobox.grid(row=1, column=0, sticky="we", pady=5)
        self.reset_button.grid(row=1, column=2, sticky="e", pady=5)


    def reset(self):
        self.value.set(self.default)

    def set_values(self, values: List[str]):
        if self.default not in values:
            values = [self.default, *values]
        self.combobox.configure(values=values)

    def get_value(self):
        value = self.value.get()
        if value == self.default:
            return None
        else:
            return value


class ItemsFilterFrame(tk.Frame):
    def __init__(self, app: App):
        super().__init__(app.window)
        self.app = app

        self.culture = FilterOptionsFrame(self, "Culture", app.model.cultures)
        self.type = FilterOptionsFrame(self, "Type", app.model.types)
        self.material = FilterOptionsFrame(self, "Material", app.model.materials)
        self.filter_button = ttk.Button(self, text="Filter", command=self.filter)
        
        self.columnconfigure(0, weight=1)
        self.culture.grid(row=0, column=0, sticky="ew", padx=10)
        self.type.grid(row=1, column=0, sticky="ew", padx=10)
        self.material.grid(row=2, column=0, sticky="ew", padx=10)
        self.filter_button.grid(row=3, column=0, sticky="", padx=10, pady=10)
    
    def filter(self):
        items = tuple(sorted(
            self.app.model.filter(
                culture=self.culture.get_value(),
                type=self.type.get_value(),
                material=self.material.get_value()
            ),
            key=lambda i: i.name
        ))
        self.app.items_table_frame.set_values(items)
        self.app.info_frame.show_info(f"Found {len(items)} items", "green")
    
    def reset(self):
        self.culture.reset()
        self.type.reset()
        self.material.reset()
    
    def update(self):
        self.culture.set_values(self.app.model.cultures)
        self.type.set_values(self.app.model.types)
        self.material.set_values(self.app.model.materials)


class ItemInfoFrame(tk.Frame):

    def __init__(self, app: App) -> None:
        super().__init__(app.window)
        self.app = app
        self.label = ttk.Label(self, text="Info", border=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.config(bg="")
        self.label.grid(row=0, column=0, sticky="nswe")
        self.label.config(background="gray")
        self.label.config(anchor="center")
        self.after_id = ""
        
    def reset(self):
        self.label.config(background="gray")
        self.label.config(text="info")

    def show_info(self, text, color):
        self.label.config(text=text)
        self.label.config(background=color)
        if self.after_id:
            self.app.window.after_cancel(self.after_id)
        self.after_id = self.app.window.after(2000, self.reset)


class SourcesListFrame(tk.Frame):
    def __init__(self, container: tk.Frame):
        super().__init__(container)
        self.values: List[str] = []
        self.label = ttk.Label(self, text="Sources List", anchor="center", font="bold", relief="raised")
        self.list_box = tk.Listbox(self, selectmode=tk.SINGLE)
        self.h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.list_box.xview)
        self.v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.list_box.yview)
        self.list_box.configure(xscrollcommand=self.h_scrollbar.set)
        self.list_box.configure(yscrollcommand=self.v_scrollbar.set)

        self.columnconfigure(0, weight=1000)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1000)
        self.rowconfigure(3, weight=1)

        self.label.grid(row=1, column=0, columnspan=2, sticky="wen")
        self.list_box.grid(row=2, column=0, columnspan=1, sticky="nwes")
        self.h_scrollbar.grid(row=2, column=0, columnspan=2, sticky="wes")
        self.v_scrollbar.grid(row=2, column=1, columnspan=1, sticky="nse")
    
    def insert(self, value: str):
        if value not in self.values:
            self.list_box.insert(tk.END, value)
            self.values.append(value)
    
    def delete(self, value: str):
        if value not in self.values:
            return
        self.values.remove(value)
        self.list_box.delete(0, tk.END)
        for value in self.values:
            self.list_box.insert(value)
    
    def get_selected(self):
        selected = self.list_box.curselection()
        if not selected:
            return None
        else:
            return self.list_box.get(selected[0])

class SourcesFrame(tk.Frame):
    def __init__(self, app: App):
        super().__init__(app.window)
        
        self.sources_list = []
        self.app = app
        self.config(background="red")
        self.add_file_button = ttk.Button(self, text="File", command=self.on_add_file)
        self.add_dir_button = ttk.Button(self, text="Directory", command=self.on_add_dir)
        self.remove_button = ttk.Button(self, text="Remove", command=self.on_remove)
        self.load_button = ttk.Button(self, text="Load", command=self.on_load)
        self.sources_list = SourcesListFrame(self)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=100)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.sources_list.grid(row=0, column=0, sticky="nwes", columnspan=2)
        self.add_file_button.grid(row=1, column=0, sticky="nwes")
        self.add_dir_button.grid(row=1, column=1, sticky="nwes")
        self.remove_button.grid(row=2, column=0, sticky="nwes", columnspan=2)
        self.load_button.grid(row=3, column=0, sticky="nwes", columnspan=2)
        for source in self.app.model.sources:
            self.sources_list.insert(source)

    def add_source(self, path: str):
        self.sources_list.insert(path)

    def on_add_file(self):
        filenames = filedialog.askopenfilenames()
        for filename in filenames:
            self.add_source(filename)

    def on_add_dir(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.add_source(dirname)

    def on_remove(self):
        selected = self.sources_list.get_selected()
        if selected:
            self.sources_list.delete(selected)

    def on_load(self):
        self.app.model.load(self.sources_list.values)
        self.app.items_filter_frame.update()
        self.app.items_filter_frame.reset()
        self.app.items_filter_frame.filter()


class App():
    def __init__(self, model: Model) -> None:
        self.model = model
        self.window = tk.Tk()
        self.window.title("Bannerlord Items Explorer")
        self.width = self.window.winfo_screenwidth() // 2
        self.height = self.window.winfo_screenheight() // 1
        self.window.geometry(f"{self.width}x{self.height}+{self.width}+0")
        self.window.columnconfigure(0, weight=20)
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=80)
        self.window.rowconfigure(2, weight=1)
        self.info_frame = ItemInfoFrame(self)
        self.items_filter_frame = ItemsFilterFrame(self)
        self.items_table_frame = ItemsTableFrame(self)
        self.sources_frame = SourcesFrame(self)
        self.items_table_frame.grid(row=0, column=0, sticky="nwse", rowspan=2)
        self.items_filter_frame.grid(row=0, column=1, sticky="nwse")
        self.sources_frame.grid(row=1, column=1, sticky="nwse")
        self.info_frame.grid(row=2, column=0, columnspan=2, sticky="nwse")
        self.window.config(bg="yellow")
        self.items_table_frame.set_values(model.items)
        self.window.protocol('WM_DELETE_WINDOW', self.on_close)

    def start(self):
        self.window.mainloop()

    def on_close(self):
        self.model.save_sources()
        self.window.destroy()