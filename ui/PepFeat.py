import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import ttkbootstrap

import meta
import util

os.makedirs(meta.homedir, exist_ok=True)

pos = [0.0, 0.0]
win = util.create_window(pos)

main = ttk.Frame(win)
main.pack(padx=16, pady=8)

headline = tk.StringVar()
ttk.Label(main, textvariable=headline, justify="center").pack()

notebook = ttk.Notebook(main)
notebook.pack(fill="x")

console = scrolledtext.ScrolledText(main, height=16, state="disabled")
console.pack(fill="x")

ttk.Label(main, text=meta.copyright, justify="center").pack()

sys.stdout = util.Console(console)
sys.stderr = util.Console(console)
if getattr(sys, 'frozen', False):
    threading.Thread(target=lambda: util.show_headline(headline, meta.server)).start()

import PepFeatDetect
notebook.add(PepFeatDetect.main, text="Feature Detection")

import PepFeatAlign
notebook.add(PepFeatAlign.main, text="Feature Alignment")

def on_exit():
    if (not (PepFeatDetect.running or PepFeatAlign.running)) or messagebox.askokcancel("Quit", "Task running. Quit now?"):
        PepFeatDetect.do_stop()
        PepFeatAlign.do_stop()
        win.destroy()

ttk.Button(main, text="×", command=on_exit).place(relx=1.0, rely=0.0, anchor="ne")

util.center_window(win)

tk.mainloop()
