import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

import meta
import util

os.makedirs(meta.homedir, exist_ok=True)

win = tk.Tk()
win.title(meta.name)
win.iconphoto(True, tk.PhotoImage(file=util.get_content(f"{meta.name}.png", shared=True)))
win.resizable(False, False)
main = ttk.Frame(win)
main.grid(column=0, row=0, padx=16, pady=8)

row = 0
# headline
row += 1

notebook = ttk.Notebook(main)
notebook.grid(column=0, row=row, sticky="WE")
row += 1

console = scrolledtext.ScrolledText(main, height=16, state="disabled")
console.grid(column=0, row=row, sticky="WE")
row += 1
ttk.Label(main, text=meta.copyright, justify="center").grid(column=0, row=row)

sys.stdout = util.Console(console)
sys.stderr = util.Console(console)
if getattr(sys, 'frozen', False):
    threading.Thread(target=lambda: util.show_headline(meta.server, main, 1)).start()

import PepFeatDetect
notebook.add(PepFeatDetect.main, text="Feature Detection")

import PepFeatAlign
notebook.add(PepFeatAlign.main, text="Feature Alignment")

tk.mainloop()
