import tkinter as tk
from tkinter import ttk

import meta
import util

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
task = util.Task("PepFeatAlign", vars_spec, path=meta.homedir)
V = task.vars

def run():
    task.call(V["pepfeatalign"].get(), *(V["data"].get().split(";")), "--out", V["out"].get(),
        "--ref", V["ref"].get(),
        "--len_rt", V["len_rt"].get(),
        "--error_mz", V["error_mz"].get(),
        "--error_rt", V["error_rt"].get(),
        "--bin", V["bin"].get(),
        "--factor", V["factor"].get(),
        "--scale", V["scale"].get(),
    )

util.init_form(main)
I = 0
t = (("Feature List", "*.csv"), ("All", "*.*"))
util.add_entry(main, I, "Feature List:", V["data"], "Select", util.askfiles(V["data"], V["out"], filetypes=t))
I += 1
util.add_entry(main, I, "Referred List:", V["ref"], "Select", util.askfile(V["ref"], filetypes=t))
I += 1
util.add_entry(main, I, "Min. RTime Length:", V["len_rt"], "sec")
I += 1
util.add_entry(main, I, "Mass Error:", V["error_mz"], "ppm")
I += 1
util.add_entry(main, I, "Max. RTime Error:", V["error_rt"], "sec")
I += 1
util.add_entry(main, I, "Moving Average Step:", V["bin"], "sec")
I += 1
util.add_entry(main, I, "Moving Average Factor:", V["factor"])
I += 1
util.add_entry(main, I, "Moving Average Scale:", V["scale"], "sec")
I += 1
util.add_entry(main, I, "Output Directory:", V["out"], "Select", util.askdir(V["out"]))
I += 1
task.init_ctrl(ttk.Frame(main), run).grid(column=0, row=I, columnspan=3)
I += 1
ttk.Separator(main, orient=tk.HORIZONTAL).grid(column=0, row=I, columnspan=3, sticky="EW")
ttk.Label(main, text="Advanced Configuration").grid(column=0, row=I, columnspan=3)
I += 1
util.add_entry(main, I, "PepFeatAlign:", V["pepfeatalign"], "Select", util.askfile(V["pepfeatalign"]))
I += 1
