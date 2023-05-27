import os
import tkinter as tk
from tkinter import ttk

import meta
import util

footnote = """
Note:
⧫ The `IPV` (isotopic pattern vectors) can be automatically generated and cached to specified path.
⧫ Select multiple data files using something like `Ctrl + A`.
⧫ Free feel to contact me if you have any questions :).
"""

main = ttk.Frame()
main.pack(fill="both")

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
task = util.Task("PepFeatDetect", vars_spec, path=meta.homedir)
V = task.vars

def run_thermorawread(data, out):
    task.call(*([] if util.is_windows else [V["mono"].get()]), V["thermorawread"].get(), data, out)
    return os.path.join(out, os.path.splitext(os.path.basename(data))[0] + ".ms1")

def run():
    paths = []
    for p in V["data"].get().split(";"):
        ext = os.path.splitext(p)[1].lower()
        if ext == ".raw": p = run_thermorawread(p, V["out"].get())
        paths.append(p)
    task.call(V["pepfeatdetect"].get(), *paths, "--out", V["out"].get(),
        "--proc", V["proc"].get(),
        "--ipv", V["ipv"].get(),
        "--peak", V["peak"].get(),
        "--charge", V["charge_min"].get() + ":" + V["charge_max"].get(),
        "--error", V["error"].get(),
        "--thres", V["exclusion"].get(),
        "--gap", V["gap"].get(),
    )

util.init_form(main)
I = 0
t = (("MS1", "*.ms1"), ("RAW", "*.raw"), ("All", "*.*"))
util.add_entry(main, I, "Data:", V["data"], "Select", util.askfiles(V["data"], V["out"], filetypes=t))
I += 1
t = (("IPV", "*.bson"), ("All", "*.*"))
util.add_entry(main, I, "IPV:", V["ipv"], "Select", util.askfile(V["ipv"], filetypes=t))
I += 1
util.add_entry(main, I, "Num. of Peaks:", V["peak"], "per scan")
I += 1
_, f, _ = util.add_entry(main, I, "Charge Range:", ttk.Frame(main))
ttk.Entry(f, textvariable=V["charge_min"]).pack(side="left", fill="x", expand=True)
ttk.Label(f, text="-").pack(side="left")
ttk.Entry(f, textvariable=V["charge_max"]).pack(side="left", fill="x", expand=True)
I += 1
util.add_entry(main, I, "Mass Error:", V["error"], "ppm")
I += 1
util.add_entry(main, I, "Exclusion Threshold:", V["exclusion"])
I += 1
util.add_entry(main, I, "Max. Scan Gap:", V["gap"])
I += 1
util.add_entry(main, I, "Output Directory:", V["out"], "Select", util.askdir(V["out"]))
I += 1
task.init_ctrl(ttk.Frame(main), run).grid(column=0, row=I, columnspan=3)
I += 1
ttk.Separator(main, orient=tk.HORIZONTAL).grid(column=0, row=I, columnspan=3, sticky="EW")
ttk.Label(main, text="Advanced Configuration").grid(column=0, row=I, columnspan=3)
I += 1
util.add_entry(main, I, "PepFeatDetect:", V["pepfeatdetect"], "Select", util.askfile(V["pepfeatdetect"]))
I += 1
util.add_entry(main, I, "ThermoRawRead:", V["thermorawread"], "Select", util.askfile(V["thermorawread"]))
I += 1
if not util.is_windows:
    util.add_entry(main, I, "Mono Runtime:", V["mono"], "Select", util.askfile(V["mono"]))
    I += 1
util.add_entry(main, I, "Parallelization:", V["proc"])
I += 1
ttk.Label(main, text=footnote, justify="left").grid(column=0, row=I, columnspan=3, sticky="EW")
