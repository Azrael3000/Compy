
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#           ━━━━━━━━━━━━━
#            ┏┓┏┓┳┳┓┏┓┓┏
#            ┃ ┃┃┃┃┃┃┃┗┫
#            ┗┛┗┛┛ ┗┣┛┗┛
#           ━━━━━━━━━━━━━
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Competition organization tool
#  for AIDA International
#  competitions.
#
#  Copyright 2023 - Arno Mayrhofer
#
#  Licensed under the GNU AGPL
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Authors:
#
#  - Arno Mayrhofer
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from tkinter import *
from tkinter import ttk
from tkinter import filedialog

import compy_data

class CompyGUI:

    def __init__(self, root, data):

        self.data_ = data

        root.title("COMPY v" + data.version)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(root)
        notebook.pack(pady=10, expand=True)

        # settings frame

        settings_frame = ttk.Frame(notebook, padding="3 3 12 12")
        settings_frame.grid(column=0, row=0, sticky=(N, W, E, S))

        # row 1: competition file

        ttk.Label(settings_frame, text="Competition file").grid(column=1, row=1, sticky=E)

        self.comp_file_ = StringVar()
        if data.comp_file != "":
            self.comp_file_.set(data.comp_file)
        file_entry = ttk.Entry(settings_frame, width=100, textvariable=self.comp_file_)
        file_entry.grid(column=2, row=1, sticky=(W, E))
        self.comp_file_.trace("w", self.compFileChange)

        ttk.Button(settings_frame, text="Open file", command=self.openFile).grid(column=3, row=1, sticky=W)

        # row 2 & 3:

        self.lane_style_ = StringVar()

        ttk.Label(settings_frame, text="Lane Style").grid(column=1, row=2, sticky=E)
        ttk.Radiobutton(settings_frame, text="Numeric (1, 2, ...)", value="numeric", variable=self.lane_style_).grid(column=2, row=2, sticky=W)
        ttk.Radiobutton(settings_frame, text="Alphanumeric (A, B, ...)", value="alphanumeric", variable=self.lane_style_).grid(column=2, row=3, sticky=W)
        self.lane_style_.set(self.data_.lane_style)
        self.lane_style_.trace("w", self.laneStyleChange)

        # row 4:
        ttk.Button(settings_frame, text="Refresh data", command=self.refresh).grid(column=2, row=4, sticky=W)

        for child in settings_frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

        file_entry.focus()

        # newcomer frame

        newcomer_main_frame = ttk.Frame(notebook)
        newcomer_main_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        self.newcomer_frame_ = ttk.Frame(necomer_main_frame, padding="3 3 12 12")
        self.newcomer_frame_.grid(column=0, row=0, sticky=(N, W, E, S))
        newcomer_scrollbar = ttk.Scrollbar(newcomer_main_frame, orient='vertical', command=text.yview)

        self.newcomer_select_ = []

        self.newcomer_cells_ = {}
        header = ["Last name", "First name", "Gender", "Country", "Newcomer"]
        self.newcomer_columns_ = len(header)
        for i in range(2):
            for j in range(self.newcomer_columns_):
                #f = ttk.Frame(newcomer_frame, width=20, height=20)
                #f.columnconfigure(0, weight=1)
                #f.rowconfigure(0, weight=1)
                #f['padding'] = 3
                #f['borderwidth'] = 1
                #f['relief'] = 'solid'
                #f.grid(row=i, column=j)
                b = None
                if i == 0:
                    b = ttk.Label(self.newcomer_frame_, text=header[j])
                else:
                    b = ttk.Label(self.newcomer_frame_, text="n/a")
                b.grid(row=i*2, column=j, padx=20, pady=2)
                self.newcomer_cells_[(i,j)] = b
            sep = ttk.Separator(self.newcomer_frame_, orient=HORIZONTAL)
            sep.grid(row=i*2+1, column=0, columnspan=5, sticky=(W, E))
            self.newcomer_cells_[(i, self.newcomer_columns_)] = sep


        # end frame definitions

        notebook.add(settings_frame, text='Settings')
        notebook.add(newcomer_main_frame, text='Newcomer')

    def openFile(self, *args):
        try:
            self.comp_file_.set(filedialog.askopenfilename(title = "Select file", filetypes = [("Excel files", "*.xlsx")]))
        except ValueError:
            pass

    def laneStyleChange(self, *args):
        self.data_.laneStyleChange(self.lane_style_.get())

    def compFileChange(self, *args):
        self.data_.compFileChange(self.comp_file_.get())

    def refresh(self, *args):
        self.data_.refresh()
        # remove newcomer data
        nrows = int(len(self.newcomer_cells_)/(self.newcomer_columns_+1))
        for i in range(1, nrows):
            for j in range(self.newcomer_columns_+1):
                self.newcomer_cells_[(i, j)].destroy()
        # add newcomer data
        self.newcomer_select_ = [IntVar() for i in range(self.data_.number_of_athletes)]
        for i, athlete in enumerate(self.data_.athletes):
            row = [athlete.last_name, athlete.first_name, athlete.gender, athlete.country]
            nstr_rows = len(row)
            for j in range(nstr_rows+2):
                if j <= nstr_rows:
                    b = None
                    if j < nstr_rows:
                        b = ttk.Label(self.newcomer_frame_, text=row[j])
                    else:
                        self.newcomer_select_[i]
                        b = ttk.Checkbutton(self.newcomer_frame_, onvalue=1, offvalue=0, variable=self.newcomer_select_[i], command=self.refresh_newcomer)
                    b.grid(row=(i+1)*2, column=j, padx=20, pady=2)
                    self.newcomer_cells_[(i+1, j)] = b
                else:
                    sep = ttk.Separator(self.newcomer_frame_, orient=HORIZONTAL)
                    sep.grid(row=(i+1)*2+1, column=0, columnspan=5, sticky=(W, E))
                    self.newcomer_cells_[(i+1, self.newcomer_columns_)] = sep

    def refresh_newcomer(self, *args):
        return
