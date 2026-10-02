#!/usr/bin/env python3
"""
plot_fits.py — draw CFD datapoints vs fitted GP curves for EVERY relationship.

Reads gp_build/fits/fit_results.json (stores raw data arrays alongside each fit), so any
relationship can be re-plotted without re-running CFD. Covers all 10 skew angles.

Run:  source ~/UAUV/.venv/bin/activate && python3 cfd/plot_fits.py
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
R = json.load(open(os.path.join(HERE, "..", "gp_build", "fits", "fit_results.json")))
OUT = os.path.join(HERE, "..", "gp_build", "fits", "plots")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.grid": True,
                     "grid.alpha": .3, "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE, GREEN, PURPLE = "#1E5FD8", "#DB5A0A", "#1B9E57", "#7C3AED"
WINGS = sorted(R["aero_polar_per_wing"], key=lambda w: R["aero_polar_per_wing"][w]["Lam"])
CMAP = plt.cm.viridis(np.linspace(0, .92, len(WINGS)))

def save(fig, name):
    fig.tight_layout(); p = os.path.join(OUT, name); fig.savefig(p); plt.close(fig)
    print("  ", os.path.relpath(p, HERE))

# ---- 1. ALL 10 aero drag polars overlaid (C_D vs C_L) ----
def all_polars():
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    for w, c in zip(WINGS, CMAP):
        v = R["aero_polar_per_wing"][w]
        CL = np.array(v["CL_arr"]); CD = np.array(v["CD_arr"])
        ax.scatter(CL, CD, s=16, color=c, zorder=3)
        xs = np.linspace(min(CL), max(CL), 80)
        ax.plot(xs, v["CD0"] + v["k"] * xs**2, color=c, lw=1.3,
                label=f"Λ={v['Lam']}° (k={v['k']:.2f})")
    ax.set_xlabel("$C_L$"); ax.set_ylabel("$C_D$")
    ax.set_title("Aerial drag polars, all skew angles  ($C_D=C_{D0}+k\\,C_L^2$)")
    ax.legend(frameon=False, fontsize=7, ncol=2)
    save(fig, "aero_polars_all.png")

# ---- 2. ALL 10 lift curves (C_L vs α) ----
def all_lift():
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    for w, c in zip(WINGS, CMAP):
        v = R["aero_polar_per_wing"][w]
        a = np.array(v["a_arr"]); CL = np.array(v["CL_arr"])
        ax.scatter(a, CL, s=16, color=c, zorder=3)
        ax.plot(a, v["CL0"] + v["CLa"] * a * np.pi/180, color=c, lw=1.3,
                label=f"Λ={v['Lam']}° ({v['CLa']:.2f}/rad)")
    ax.set_xlabel("angle of attack $\\alpha$ (deg)"); ax.set_ylabel("$C_L$")
    ax.set_title("Lift curves, all skew angles")
    ax.legend(frameon=False, fontsize=7, ncol=2)
    save(fig, "aero_lift_all.png")

# ---- 3. schedules vs Λ ----
def schedule(key, ylabel, title, fname, logy=False):
    d = R[key]
    L = np.array(d["Lam_deg"]); y = np.array(d["y"])
    fig, ax = plt.subplots(figsize=(4.8, 3.7))
    ax.scatter(L, y, s=30, color=BLUE, zorder=3, label="CFD")
    Ls = np.linspace(min(L), max(L), 100); mus = np.cos(np.radians(Ls))
    ax.plot(Ls, d["c"] * mus**d["a"], color=BLUE, lw=1.6,
            label=f"${d['c']:.3g}(\\cos\\Lambda)^{{{d['a']:.2f}}}$  (rms {d['rms_log']:.3f})")
    if logy: ax.set_yscale("log")
    ax.set_xlabel("skew $\\Lambda$ (deg)"); ax.set_ylabel(ylabel); ax.set_title(title)
    ax.legend(frameon=False, fontsize=8); save(fig, fname)

def k_schedule():
    v = R["aero_polar_per_wing"]
    L = np.array([v[w]["Lam"] for w in WINGS]); k = np.array([v[w]["k"] for w in WINGS])
    fig, ax = plt.subplots(figsize=(4.8, 3.7))
    ax.scatter(L, k, s=30, color=ORANGE, zorder=3); ax.plot(L, k, color=ORANGE, lw=1, alpha=.5)
    ax.set_yscale("log"); ax.set_xlabel("skew $\\Lambda$ (deg)")
    ax.set_ylabel("induced factor $k=1/(\\pi e AR)$")
    ax.set_title("Aspect-ratio collapse (0.64 → 22.9)"); save(fig, "sched_k.png")

def cl_roll():
    v = R["aero_polar_per_wing"]
    L = np.array([v[w]["Lam"] for w in WINGS])
    cl = np.array([v[w]["Cl_absmax"] for w in WINGS])
    fig, ax = plt.subplots(figsize=(4.8, 3.7))
    ax.scatter(L, cl, s=30, color=PURPLE, zorder=3); ax.plot(L, cl, color=PURPLE, lw=1, alpha=.5)
    ax.set_xlabel("skew $\\Lambda$ (deg)"); ax.set_ylabel("$|C_l|_{\\max}$ (roll)")
    ax.set_title("Roll coefficient vs skew  (near noise floor, ~$10^{-3}$)")
    save(fig, "sched_Cl_roll.png")

# ---- 4. hydro polars (stowed + deployed) ----
def hydro_polars():
    fig, ax = plt.subplots(figsize=(4.8, 3.7))
    for key, col, lab in [("HYDRO_stowed", GREEN, "stowed Λ=90"), ("HYDRO_deployed", BLUE, "deployed Λ=0")]:
        d = R[key]; CL = np.array(d["CL_arr"]); CD = np.array(d["CD_arr"])
        ax.scatter(CL, CD, s=22, color=col, zorder=3, label=f"{lab} data")
        xs = np.linspace(min(CL), max(CL), 80)
        ax.plot(xs, d["CD0"] + d["k"]*xs**2, color=col, lw=1.5,
                label=f"$C_D={d['CD0']:.3f}+{d['k']:.1f}C_L^2$")
    ax.set_xlabel("$C_L$"); ax.set_ylabel("$C_{D,w}$"); ax.set_title("Underwater polars (V_w=5 m/s)")
    ax.legend(frameon=False, fontsize=7.5); save(fig, "hydro_polars.png")

def hydro_Re():
    d = R["HYDRO_CD0_vs_Re"]
    Re = np.array(d["Re"]); CD0 = np.array(d["CD0"])
    fig, ax = plt.subplots(figsize=(4.8, 3.7))
    ax.scatter(Re, CD0, s=30, color=GREEN, zorder=3, label="CFD")
    xs = np.linspace(min(Re), max(Re), 100)
    ax.plot(xs, d["c"]*xs**d["a"], color=GREEN, lw=1.6, label=f"${d['c']:.3g}Re^{{{d['a']:.3f}}}$")
    ax.set_xscale("log"); ax.set_xlabel("$Re$"); ax.set_ylabel("$C_{D0,w}$")
    ax.set_title("Underwater zero-lift drag vs Reynolds"); ax.legend(frameon=False, fontsize=8)
    save(fig, "hydro_CD0_Re.png")

def trim():
    d = R["HYDRO_stowed_trim"]; a = np.array(d["a_arr"]); CL = np.array(d["CL_arr"])
    fig, ax = plt.subplots(figsize=(4.8, 3.7))
    ax.scatter(a, CL, s=22, color=ORANGE, zorder=3, label="CFD")
    xs = np.linspace(min(a), max(a), 100)
    ax.plot(xs, d["C_L0"] + d["C_Lalpha_uw"]*xs*np.pi/180, color=ORANGE, lw=1.6,
            label=f"$dC_L/d\\alpha={d['C_Lalpha_uw']:.3f}$/rad")
    ax.set_xlabel("$\\alpha$ (deg)"); ax.set_ylabel("$C_{L,uw}$")
    ax.set_title("Stowed-wing trim lift (fine α)"); ax.legend(frameon=False, fontsize=8)
    save(fig, "hydro_trim.png")

# ---- 5. cavitation SPLIT by config ----
def cavitation_split():
    fig, ax = plt.subplots(figsize=(5.0, 3.9))
    for cfg, col in [("CAVITATION_stowed", GREEN), ("CAVITATION_deployed", BLUE)]:
        e = R[cfg]; CL = np.array(e["CL"]); ncp = np.array(e["negCp"]); ok = np.isfinite(CL)
        ax.scatter(CL[ok], ncp[ok], s=26, color=col, zorder=3, label=f"{e['config']}")
        if "fit" in e:
            xs = np.linspace(np.nanmin(CL), np.nanmax(CL), 60)
            ax.plot(xs, e["fit"]["c"]*xs**e["fit"]["a"], color=col, lw=1.5)
        else:
            ax.axhline(e["negCp_mean"], color=col, lw=1.3, ls="--")
    ax.set_xlabel("$C_L$"); ax.set_ylabel("$-C_{p,\\min}$")
    ax.set_title("Cavitation suction peak — two configs (was wrongly merged)")
    ax.legend(frameon=False, fontsize=7.5); save(fig, "cavitation_split.png")

if __name__ == "__main__":
    print("Plots →", os.path.relpath(OUT, HERE))
    all_polars(); all_lift()
    schedule("AERO_schedule_CLalpha", "$C_{L\\alpha}$ (/rad)",
             "Lift-slope vs skew — validates $\\propto\\cos\\Lambda$", "sched_CLalpha.png")
    k_schedule(); cl_roll()
    hydro_polars(); hydro_Re(); trim()
    cavitation_split()
    print("done —", len(os.listdir(OUT)), "figures")
