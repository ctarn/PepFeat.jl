import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog

import meta
import util

handles = []
running = False
skip_rest = False

path_autosave = os.path.join(meta.homedir, "autosave_detect.task")

footnote = """
Note:
⧫ Please try something like `Ctrl + A` to select multiple data files.
⧫ `IPV` (isotopic pattern vectors) can be automatically generated and cached to specified path.
⧫ Free feel to contact me if you have any questions :).
"""

main = ttk.Frame()
main.grid(sticky="SNWE")

if util.is_darwin:
    path_mono = "/Library/Frameworks/Mono.framework/Versions/Current/Commands/mono"
else:
    path_mono = "mono"

vars_spec = {
    "data": {"type": tk.StringVar, "value": ""},
    "ipv": {"type": tk.StringVar, "value": os.path.join(meta.homedir, "IPV.bson")},
    "peak": {"type": tk.StringVar, "value": "4000"},
    "charge_min": {"type": tk.StringVar, "value": "2"},
    "charge_max": {"type": tk.StringVar, "value": "6"},
    "error": {"type": tk.StringVar, "value": "10.0"},
    "exclusion": {"type": tk.StringVar, "value": "1.0"},
    "gap": {"type": tk.StringVar, "value": "16"},
    "out": {"type": tk.StringVar, "value": ""},
    "pepfeatdetect": {"type": tk.StringVar, "value": util.get_content("PepFeat", "bin", "PepFeatDetect")},
    "thermorawread": {"type": tk.StringVar, "value": util.get_content("ThermoRawRead", "ThermoRawRead.exe", shared=True)},
    "mono": {"type": tk.StringVar, "value": path_mono},
    "proc": {"type": tk.StringVar, "value": "4"},
}
vars = {k: v["type"](value=v["value"]) for k, v in vars_spec.items()}
util.load_task(path_autosave, vars)

row = 0
ttk.Label(main, width=20 if util.is_windows else 16).grid(column=0, row=row)
ttk.Label(main, width=80 if util.is_windows else 60).grid(column=1, row=row)
ttk.Label(main, width=12 if util.is_windows else 10).grid(column=2, row=row)

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
ttk.Entry(main, textvariable=vars["data"]).grid(column=1, row=row, **util.sty_entry)
ttk.Button(main, text="Select", command=do_select_data).grid(column=2, row=row, **util.sty_button)
row += 1

def do_select_model():
    path = filedialog.askopenfilename(filetypes=(("IPV", "*.bson"), ("All", "*.*")))
    if len(path) > 0: vars["ipv"].set(path)

ttk.Label(main, text="IPV:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["ipv"]).grid(column=1, row=row, **util.sty_entry)
ttk.Button(main, text="Select", command=do_select_model).grid(column=2, row=row, **util.sty_button)
row += 1

ttk.Label(main, text="Num. of Peaks:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["peak"]).grid(column=1, row=row, **util.sty_entry)
ttk.Label(main, text="per scan").grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Charge Range:").grid(column=0, row=row, sticky="W")
frm_charge = ttk.Frame(main)
frm_charge.grid(column=1, row=row, sticky="WE")
ttk.Entry(frm_charge, textvariable=vars["charge_min"]).grid(column=0, row=0, **util.sty_entry)
ttk.Label(frm_charge, text=" - ").grid(column=1, row=0, sticky="WE")
ttk.Entry(frm_charge, textvariable=vars["charge_max"]).grid(column=2, row=0, **util.sty_entry)
row += 1

ttk.Label(main, text="Mass Error:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["error"]).grid(column=1, row=row, **util.sty_entry)
ttk.Label(main, text="ppm").grid(column=2, row=row, sticky="W")
row += 1

ttk.Label(main, text="Exclusion Threshold:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["exclusion"]).grid(column=1, row=row, **util.sty_entry)
row += 1

ttk.Label(main, text="Max. Scan Gap:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["gap"]).grid(column=1, row=row, **util.sty_entry)
row += 1

def do_select_out():
    path = filedialog.askdirectory()
    if len(path) > 0: vars["out"].set(path)

ttk.Label(main, text="Output Directory:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["out"]).grid(column=1, row=row, **util.sty_entry)
ttk.Button(main, text="Select", command=do_select_out).grid(column=2, row=row, **util.sty_button)
row += 1

def run_thermorawread(data, out):
    cmd = [vars["thermorawread"].get(), data, out]
    if not util.is_windows:
        cmd = [vars["mono"].get()] + cmd
    util.run_cmd(cmd, handles, skip_rest)
    return os.path.join(out, os.path.splitext(os.path.basename(data))[0] + ".ms1")

def run_pepfeatdetect(path):
    cmd = [
        vars["pepfeatdetect"].get(),
        "--proc", vars["proc"].get(),
        "--ipv", vars["ipv"].get(),
        "--peak", vars["peak"].get(),
        "--charge", vars["charge_min"].get() + ":" + vars["charge_max"].get(),
        "--error", vars["error"].get(),
        "--thres", vars["exclusion"].get(),
        "--gap", vars["gap"].get(),
        "--out", vars["out"].get(),
        path,
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
        util.save_task(os.path.join(path, "PepFeatDetect.task"), vars)
    else:
        print("`Output Directory` is required")

def do_run():
    btn_run.config(state="disabled")
    global handles, running, skip_rest
    running = True
    skip_rest = False
    do_save()
    for p in vars["data"].get().split(";"):
        ext = os.path.splitext(p)[1].lower()
        if ext == ".raw":
            p = run_thermorawread(p, vars["out"].get())
        run_pepfeatdetect(p)
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
    print("PepFeatDetect stopped.")

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

def do_select_pepfeatdetect():
    path = filedialog.askopenfilename()
    if len(path) > 0: vars["pepfeatdetect"].set(path)

ttk.Label(main, text="PepFeatDetect:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["pepfeatdetect"]).grid(column=1, row=row, **util.sty_entry)
ttk.Button(main, text="Select", command=do_select_pepfeatdetect).grid(column=2, row=row, **util.sty_button)
row += 1

def do_select_thermorawread():
    path = filedialog.askopenfilename()
    if len(path) > 0: vars["thermorawread"].set(path)

ttk.Label(main, text="ThermoRawRead:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["thermorawread"]).grid(column=1, row=row, **util.sty_entry)
ttk.Button(main, text="Select", command=do_select_thermorawread).grid(column=2, row=row, **util.sty_button)
row += 1

def do_select_mono():
    path = filedialog.askopenfilename()
    if len(path) > 0: vars["mono"].set(path)

if not util.is_windows:
    ttk.Label(main, text="Mono Runtime:").grid(column=0, row=row, sticky="W")
    ttk.Entry(main, textvariable=vars["mono"]).grid(column=1, row=row, **util.sty_entry)
    ttk.Button(main, text="Select", command=do_select_mono).grid(column=2, row=row, **util.sty_button)
    row += 1

ttk.Label(main, text="Parallelization:").grid(column=0, row=row, sticky="W")
ttk.Entry(main, textvariable=vars["proc"]).grid(column=1, row=row, **util.sty_entry)
row += 1

ttk.Label(main, text=footnote, justify="left").grid(column=0, row=row, columnspan=3, sticky="WE")
