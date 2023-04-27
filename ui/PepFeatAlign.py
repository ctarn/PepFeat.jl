import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog

import meta
import util

handles = []
running = False
skip_rest = False

path_autosave = os.path.join(meta.homedir, "autosave_align.task")

footnote = """
Note:
⧫ This feature is only experimental currently.
"""

main = ttk.Frame()
main.grid(sticky="SNWE")

vars_spec = {
    "data": {"type": tk.StringVar, "value": ""},
    "ref": {"type": tk.StringVar, "value": ""},
    "len_rt": {"type": tk.StringVar, "value": "4.0"},
    "error_mz": {"type": tk.StringVar, "value": "1.0"},
    "error_rt": {"type": tk.StringVar, "value": "600.0"},
    "bin": {"type": tk.StringVar, "value": "1.0"},
    "factor": {"type": tk.StringVar, "value": "0.1"},
    "scale": {"type": tk.StringVar, "value": "64"},
    "out": {"type": tk.StringVar, "value": ""},
    "pepfeatalign": {"type": tk.StringVar, "value": util.get_content("PepFeat", "bin", "PepFeatAlign")},
}
vars = {k: v["type"](value=v["value"]) for k, v in vars_spec.items()}
util.load_task(path_autosave, vars)

row = 0
ttk.Label(main, width=20 if util.is_windows else 16).grid(column=0, row=row)
ttk.Label(main, width=80 if util.is_windows else 60).grid(column=1, row=row)
ttk.Label(main, width=12 if util.is_windows else 10).grid(column=2, row=row)

def do_select_data():
    filetypes = (("Feature List", "*.csv"), ("All", "*.*"))
    files = filedialog.askopenfilenames(filetypes=filetypes)
    if len(files) == 0:
        return None
    elif len(files) > 1:
        print("multiple data selected:")
        for file in files: print(">>", file)
    vars["data"].set(";".join(files))
    if len(vars["data"].get()) > 0 and len(vars["out"].get()) == 0:
        vars["out"].set(os.path.join(os.path.dirname(files[0]), "out"))

ttk.Label(main, text="Feature List:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["data"]).grid(column=1, row=row, **util.sty_entry)
ttk.Button(main, text="Select", command=do_select_data).grid(column=2, row=row, **util.sty_button)
row += 1

def do_select_ref():
    filetypes = (("Feature List", "*.csv"), ("All", "*.*"))
    path = filedialog.askopenfilename(filetypes=filetypes)
    if len(path) > 0: vars["ref"].set(path)

ttk.Label(main, text="Referred List:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["ref"]).grid(column=1, row=row, **util.sty_entry)
ttk.Button(main, text="Select", command=do_select_ref).grid(column=2, row=row, **util.sty_button)
row += 1

ttk.Label(main, text="Min RTime Length:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["len_rt"]).grid(column=1, row=row, **util.sty_entry)
ttk.Label(main, text="sec").grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Mass Error:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["error_mz"]).grid(column=1, row=row, **util.sty_entry)
ttk.Label(main, text="ppm").grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Max RTime Error:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["error_rt"]).grid(column=1, row=row, **util.sty_entry)
ttk.Label(main, text="sec").grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Moving Average Step:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["bin"]).grid(column=1, row=row, **util.sty_entry)
ttk.Label(main, text="sec").grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Moving Average Factor:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["factor"]).grid(column=1, row=row, **util.sty_entry)
row += 1

ttk.Label(main, text="Moving Average Scale:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["scale"]).grid(column=1, row=row, **util.sty_entry)
ttk.Label(main, text="sec").grid(column=2, row=row, sticky="W")
row += 1

def do_select_out():
    path = filedialog.askdirectory()
    if len(path) > 0: vars["out"].set(path)

ttk.Label(main, text="Output Directory:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["out"]).grid(column=1, row=row, **util.sty_entry)
ttk.Button(main, text="Select", command=do_select_out).grid(column=2, row=row, **util.sty_button)
row += 1

def run_pepfeatalign(path):
    cmd = [
        vars["pepfeatalign"].get(),
        "--ref", vars["ref"].get(),
        "--len_rt", vars["len_rt"].get(),
        "--error_mz", vars["error_mz"].get(),
        "--error_rt", vars["error_rt"].get(),
        "--bin", vars["bin"].get(),
        "--factor", vars["factor"].get(),
        "--scale", vars["scale"].get(),
        "--out", vars["out"].get(),
        path,
    ]
    util.run_cmd(cmd, handles, skip_rest)

def do_load():
    path = filedialog.askopenfilename(filetypes=(("Configuration", "*.task"), ("All", "*.*")))
    if len(path) > 0: util.load_task(path)

def do_save():
    util.save_task(path_autosave, {k: v for k, v in vars.items() if v.get() != vars_spec[k]["value"]})
    path = vars["out"].get()
    if len(path) > 0:
        os.makedirs(path, exist_ok=True)
        util.save_task(os.path.join(path, "PepFeatAlign.task"), vars)
    else:
        print("`Output Directory` is required")

def do_run():
    btn_run.config(state="disabled")
    global handles, running, skip_rest
    running = True
    skip_rest = False
    do_save()
    for p in vars["data"].get().split(";"):
        run_pepfeatalign(p)
    running = False
    btn_run.config(state="normal")

def do_stop():
    global handles, running, skip_rest
    skip_rest = True
    for job in handles:
        if job.poll() is None:
            job.terminate()
    running = False
    handles.clear()
    btn_run.config(state="normal")
    print("PepFeatAlign stopped.")

frm_btn = ttk.Frame(main)
frm_btn.grid(column=0, row=row, columnspan=3)
ttk.Button(frm_btn, text="Load Task", command=do_load).grid(column=0, row=0, padx=16, pady=8)
ttk.Button(frm_btn, text="Save Task", command=do_save).grid(column=1, row=0, padx=16, pady=8)
btn_run = ttk.Button(frm_btn, text="Run Task", command=lambda: threading.Thread(target=do_run).start())
btn_run.grid(column=2, row=0, padx=16, pady=8)
ttk.Button(frm_btn, text="Stop Task", command=lambda: threading.Thread(target=do_stop).start()).grid(column=3, row=0, padx=16, pady=8)
row += 1

ttk.Separator(main, orient=tk.HORIZONTAL).grid(column=0, row=row, columnspan=3, sticky="WE")
ttk.Label(main, text="Advanced Configuration").grid(column=0, row=row, columnspan=3)
row += 1

def do_select_pepfeatalign():
    path = filedialog.askopenfilename()
    if len(path) > 0: vars["pepfeatalign"].set(path)

ttk.Label(main, text="PepFeatAlign:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["pepfeatalign"]).grid(column=1, row=row, **util.sty_entry)
ttk.Button(main, text="Select", command=do_select_pepfeatalign).grid(column=2, row=row, **util.sty_button)
row += 1
