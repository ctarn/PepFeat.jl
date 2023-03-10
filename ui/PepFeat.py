import os
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

import meta
import util

os.makedirs(meta.homedir, exist_ok=True)
path_autosave = os.path.join(meta.homedir, "autosave.task")

win = tk.Tk()
win.title(meta.name)
win.iconphoto(True, tk.PhotoImage(file=util.get_content(f"{meta.name}.png", shared=True)))
win.resizable(False, False)
main = ttk.Frame(win)
main.grid(column=0, row=0, padx=16, pady=8)

if util.is_darwin:
    path_mono = "/Library/Frameworks/Mono.framework/Versions/Current/Commands/mono"
else:
    path_mono = "mono"

vars_spec = {
    "data": {"type": tk.StringVar, "value": ""},
    "model": {"type": tk.StringVar, "value": os.path.join(meta.homedir, "IPV.bson")},
    "exclusion": {"type": tk.StringVar, "value": "1.0"},
    "error": {"type": tk.StringVar, "value": "10.0"},
    "gap": {"type": tk.StringVar, "value": "16"},
    "peak": {"type": tk.StringVar, "value": "4000"},
    "charge_min": {"type": tk.StringVar, "value": "2"},
    "charge_max": {"type": tk.StringVar, "value": "6"},
    "out": {"type": tk.StringVar, "value": ""},
    "pepfeat": {"type": tk.StringVar, "value": util.get_content("PepFeat", "bin", "PepFeatDetect")},
    "thermorawread": {"type": tk.StringVar, "value": util.get_content("ThermoRawRead", "ThermoRawRead.exe", shared=True)},
    "mono": {"type": tk.StringVar, "value": path_mono},
    "proc": {"type": tk.StringVar, "value": "4"},
}
vars = {k: v["type"](value=v["value"]) for k, v in vars_spec.items()}

row = 0
# headline
row += 1

def do_select_data():
    filetypes = (("MS1", "*.ms1"), ("RAW", "*.raw"), ("All", "*.*"))
    files = filedialog.askopenfilenames(filetypes=filetypes)
    if len(files) == 0:
        return None
    elif len(files) > 1:
        print("multiple data selected:")
        for file in files: print(">>", file)
    vars["data"].set(";".join(files))
    if len(vars["data"].get()) > 0 and len(vars["out"].get()) == 0:
        vars["out"].set(os.path.join(os.path.dirname(files[0]), "out"))

ttk.Label(main, text="Data:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["data"]).grid(column=1, row=row, sticky="WE")
ttk.Button(main, text="Select", command=do_select_data).grid(column=2, row=row, sticky="W")
row += 1

def do_select_model():
    path = filedialog.askopenfilename(filetypes=(("Model", "*.bson"), ("All", "*.*")))
    if len(path) > 0: vars["model"].set(path)

ttk.Label(main, text="Model:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["model"]).grid(column=1, row=row, sticky="WE")
ttk.Button(main, text="Select", command=do_select_model).grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Exclusion Threshold:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["exclusion"]).grid(column=1, row=row, sticky="WE")
row += 1

ttk.Label(main, text="Mass Error:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["error"]).grid(column=1, row=row, sticky="WE")
ttk.Label(main, text="ppm").grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Max. Scan Gap:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["gap"]).grid(column=1, row=row, sticky="WE")
row += 1

ttk.Label(main, text="Num. of Peaks:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["peak"]).grid(column=1, row=row, sticky="WE")
ttk.Label(main, text="per Scan").grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Charge Range:").grid(column=0, row=row, sticky="W")
frm_charge = ttk.Frame(main)
frm_charge.grid(column=1, row=row, sticky="WE")
ttk.Entry(frm_charge, textvariable=vars["charge_min"]).grid(column=0, row=0, sticky="WE")
ttk.Label(frm_charge, text=" - ").grid(column=1, row=0, sticky="WE")
ttk.Entry(frm_charge, textvariable=vars["charge_max"]).grid(column=2, row=0, sticky="WE")
row += 1

def do_select_out():
    path = filedialog.askdirectory()
    if len(path) > 0: vars["out"].set(path)

ttk.Label(main, text="Output Directory:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["out"]).grid(column=1, row=row, sticky="WE")
ttk.Button(main, text="Select", command=do_select_out).grid(column=2, row=row, sticky="W")
row += 1

def run_thermorawread(data, out):
    cmd = [vars["thermorawread"].get(), data, out]
    if not util.is_windows:
        cmd = [vars["mono"].get()] + cmd
    util.run_cmd(cmd)
    return os.path.join(out, os.path.splitext(os.path.basename(data))[0] + ".ms1")

def run_pepfeat(path):
    cmd = [
        vars["pepfeat"].get(),
        path,
        "--proc", vars["proc"].get(),
        "-m", vars["model"].get(),
        "-t", vars["exclusion"].get(),
        "-e", vars["error"].get(),
        "-g", vars["gap"].get(),
        "-p", vars["peak"].get(),
        "-z", vars["charge_min"].get() + ":" + vars["charge_max"].get(),
        "-o", vars["out"].get(),
    ]
    util.run_cmd(cmd)

def do_load():
    path = filedialog.askopenfilename(filetypes=(("Configuration", "*.task"), ("All", "*.*")))
    if len(path) > 0: util.load_task(path)

def do_save():
    util.save_task(path_autosave, {k: v for k, v in vars.items() if v.get() != vars_spec[k]["value"]})
    path = vars["out"].get()
    if len(path) > 0:
        os.makedirs(path, exist_ok=True)
        util.save_task(os.path.join(path, "PepFeat.task"), vars)
    else:
        print("`Output Directory` is required")

def do_run():
    btn_run.config(state="disabled")
    do_save()
    for p in vars["data"].get().split(";"):
        ext = os.path.splitext(p)[1].lower()
        if ext == ".raw":
            p = run_thermorawread(p, vars["out"].get())
        run_pepfeat(p)
    btn_run.config(state="normal")

frm_btn = ttk.Frame(main)
frm_btn.grid(column=0, row=row, columnspan=3)
ttk.Button(frm_btn, text="Load Task", command=do_load).grid(column=0, row=0, padx=16, pady=8)
ttk.Button(frm_btn, text="Save Task", command=do_save).grid(column=1, row=0, padx=16, pady=8)
btn_run = ttk.Button(frm_btn, text="Save & Run", command=lambda: threading.Thread(target=do_run).start())
btn_run.grid(column=2, row=0, padx=16, pady=8)
row += 1

console = scrolledtext.ScrolledText(main, height=16)
console.config(state="disabled")
console.grid(column=0, row=row, columnspan=3, sticky="WE")
row += 1

ttk.Label(main, text="Advanced Configuration").grid(column=0, row=row, columnspan=3)
row += 1

def do_select_pepfeat():
    path = filedialog.askopenfilename()
    if len(path) > 0: vars["pepfeat"].set(path)

ttk.Label(main, text="PepFeat:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["pepfeat"]).grid(column=1, row=row, sticky="WE")
ttk.Button(main, text="Select", command=do_select_pepfeat).grid(column=2, row=row, sticky="W")
row += 1

def do_select_thermorawread():
    path = filedialog.askopenfilename()
    if len(path) > 0: vars["thermorawread"].set(path)

ttk.Label(main, text="ThermoRawRead:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["thermorawread"]).grid(column=1, row=row, sticky="WE")
ttk.Button(main, text="Select", command=do_select_thermorawread).grid(column=2, row=row, sticky="W")
row += 1

def do_select_mono():
    path = filedialog.askopenfilename()
    if len(path) > 0: vars["mono"].set(path)

if not util.is_windows:
    ttk.Label(main, text="Mono Runtime:").grid(column=0, row=row, sticky="W")
    ttk.Entry(main, textvariable=vars["mono"]).grid(column=1, row=row, sticky="WE")
    ttk.Button(main, text="Select", command=do_select_mono).grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Parallelization:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["proc"]).grid(column=1, row=row, sticky="WE")
row += 1

ttk.Label(main, text=meta.copyright, justify="center").grid(column=0, row=row, columnspan=3)

sys.stdout = util.Console(console)
sys.stderr = util.Console(console)

if getattr(sys, 'frozen', False):
    threading.Thread(target=lambda: util.show_headline(meta.server, main, 3)).start()

util.load_task(path_autosave, vars)

tk.mainloop()
