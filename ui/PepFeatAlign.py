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

main = ttk.Frame()
main.pack(fill="both")

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
util.init_form(main)

t = (("Feature List", "*.csv"), ("All", "*.*"))
def do_select_data():
    files = filedialog.askopenfilenames(filetypes=t)
    if len(files) == 0:
        return None
    elif len(files) > 1:
        print("multiple data selected:")
        for file in files: print(">>", file)
    vars["data"].set(";".join(files))
    if len(vars["data"].get()) > 0 and len(vars["out"].get()) == 0:
        vars["out"].set(os.path.join(os.path.dirname(files[0]), "out"))

util.add_entry(main, row, "Feature List:", vars["data"], "Select", do_select_data)
row += 1

util.add_entry(main, row, "Referred List:", vars["ref"], "Select", util.askfile(vars["ref"], filetypes=t))
row += 1

util.add_entry(main, row, "Min. RTime Length:", vars["len_rt"], "sec")
row += 1

util.add_entry(main, row, "Mass Error:", vars["error_mz"], "ppm")
row += 1

util.add_entry(main, row, "Max. RTime Error:", vars["error_rt"], "sec")
row += 1

util.add_entry(main, row, "Moving Average Step:", vars["bin"], "sec")
row += 1

util.add_entry(main, row, "Moving Average Factor:", vars["factor"])
row += 1

util.add_entry(main, row, "Moving Average Scale:", vars["scale"], "sec")
row += 1

util.add_entry(main, row, "Output Directory:", vars["out"], "Select", util.askdir(vars["out"]))
row += 1

def run_pepfeatalign(paths):
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
        *paths,
    ]
    util.run_cmd(cmd, handles, skip_rest)

def do_load():
    path = filedialog.askopenfilename(filetypes=(("Configuration", "*.task"), ("All", "*.*")))
    if len(path) > 0: util.load_task(path, vars)

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
    run_pepfeatalign(vars["data"].get().split(";"))
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

ttk.Separator(main, orient=tk.HORIZONTAL).grid(column=0, row=row, columnspan=3, sticky="EW")
ttk.Label(main, text="Advanced Configuration").grid(column=0, row=row, columnspan=3)
row += 1

util.add_entry(main, row, "PepFeatAlign:", vars["pepfeatalign"], "Select", util.askfile(vars["pepfeatalign"]))
row += 1
