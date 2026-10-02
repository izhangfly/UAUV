#!/usr/bin/env python3
"""
fit_gp.py — Fit UAUV CFD sweep data into GP-compatible forms (gpfit).

Reads the CSV databases (NOT hard-coded numbers), extracts drag polars, lift
slopes, roll schedule, cavitation suction peak, and fits Λ-schedules with gpfit.
Writes:
  gp_build/fits/fit_results.json   — machine-readable (coeffs, errors, data arrays)
  stdout                            — human-readable report

Run:  source ~/UAUV/.venv/bin/activate && python3 cfd/fit_gp.py
"""
import csv, json, os
from collections import defaultdict
import numpy as np
from gpfit.fit import fit

DB = os.path.join(os.path.dirname(__file__), "database")
OUT = os.path.join(os.path.dirname(__file__), "..", "gp_build", "fits")
os.makedirs(OUT, exist_ok=True)
DEG = np.pi / 180.0

def load(name):
    with open(os.path.join(DB, name)) as f:
        return [r for r in csv.DictReader(f)]

def lam_deg(wing):                       # skew angle Λ (deg): 0=deployed .. 90=stowed
    return 90 - int(wing.replace("Wing", ""))

def linreg(x, y):                        # y = b0 + b1 x ; returns (b0, b1, R2)
    x = np.asarray(x, float); y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    A = np.vstack([np.ones_like(x), x]).T
    coef = np.linalg.solve(A.T @ A, A.T @ y)   # normal equations (robust vs LAPACK lstsq)
    yhat = A @ coef
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    R2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return coef[0], coef[1], R2

def monofit(u, w):
    """Monomial w = c·u^a. Equivalent to gpfit max-affine K=1: a log-log least-squares
    minimising RMS log-error. Robust (no SVD initialiser)."""
    lu = np.log(np.asarray(u, float)); lw = np.log(np.asarray(w, float))
    b0, b1, _ = linreg(lu, lw)
    rms_log = float(np.sqrt(np.mean((lw - (b0 + b1 * lu)) ** 2)))
    return dict(c=float(np.exp(b0)), a=float(b1), rms_log=rms_log)

def smafit(u, w, K=2, seed=1):           # posynomial via gpfit softmax-affine
    x = np.log(np.asarray(u, float)).reshape(1, -1)
    y = np.log(np.asarray(w, float))
    f = fit(x, y, K, "sma", seed=seed)
    return f, dict(rms_log=float(f.errors["rms_log"]),
                   params=np.asarray(f.params).ravel().tolist())

results = {"meta": {"source": "cfd/database/*.csv", "convention": "Lambda=90-WingXX deg; 0=deployed"}}

# ===================================================================
# 1. AERO — per-wing drag polar (C_D = C_D0 + k C_L^2) & lift slope
# ===================================================================
aero = load("aero_results.csv")
byw = defaultdict(list)
for r in aero:
    if r["status"] not in ("ok", "recovered"):
        continue
    byw[r["wing"]].append((float(r["alpha"]), float(r["C_D"]), float(r["C_L"]),
                           float(r["CmRoll"] or 0)))

aero_polar = {}
for w, d in byw.items():
    d.sort()
    a = np.array([p[0] for p in d]) * DEG
    CD = np.array([p[1] for p in d])
    CL = np.array([p[2] for p in d])
    Cl = np.array([p[3] for p in d])
    CD0, k, R2p = linreg(CL ** 2, CD)          # polar
    CL0, CLa, R2l = linreg(a, CL)              # lift curve
    aero_polar[w] = dict(Lam=lam_deg(w), CD0=float(CD0), k=float(k), R2_polar=float(R2p),
                         CL0=float(CL0), CLa=float(CLa), R2_lift=float(R2l),
                         Cl_absmax=float(np.max(np.abs(Cl))),
                         Cl_at_a4=float(Cl[np.argmin(np.abs(a - 4 * DEG))]),
                         CL_arr=CL.tolist(), CD_arr=CD.tolist(), a_arr=(a / DEG).tolist(),
                         Cl_arr=Cl.tolist())
results["aero_polar_per_wing"] = aero_polar

# design-point (deployed = Wing90, Λ=0)
dep = aero_polar["Wing90"]

def posy_polar(CL, CD):
    """GP-legal C_D(C_L). Try 2-term SMA posynomial (seed sweep); fall back to monomial.
    Over the measured (upper-branch) C_L range the polar is ~power-law, so a monomial
    C_D=c·C_L^a is GP-legal and accurate near the operating point."""
    CL = np.asarray(CL, float); CD = np.asarray(CD, float)
    pos = CL > 1e-4                          # monomial C_D(C_L) only on positive (upper) branch
    CL, CD = CL[pos], CD[pos]
    for s in range(1, 40):
        try:
            _, f = smafit(CL, CD, 2, seed=s)
            if np.isfinite(f["rms_log"]):
                f["type"] = "SMA-2"; return f
        except Exception:
            continue
    m = monofit(CL, CD)                       # robust fallback: C_D = c·C_L^a
    return dict(type="monomial", rms_log=m["rms_log"],
                params=[m["c"], m["a"]], form=f"C_D = {m['c']:.4g}·C_L^{m['a']:.3f}")

# operating point (cruise ~ α=0) and GP-legal posynomial polar
def op_point(v):
    i0 = int(np.argmin(np.abs(np.array(v["a_arr"]))))
    return dict(CL_cruise=v["CL_arr"][i0], CD_cruise=v["CD_arr"][i0], alpha0=v["a_arr"][i0])

dep_posy = posy_polar(dep["CL_arr"], dep["CD_arr"])
results["AERO_deployed"] = dict(
    C_D0_a=dep["CD0"], k_a=dep["k"], C_Lalpha_a=dep["CLa"],
    **op_point(dep),
    posy_CD_of_CL=dict(rms_log=dep_posy["rms_log"], params=dep_posy["params"]),
    note="deployed Λ=0 (Wing90). C_D0<0 is the NACA-3612 camber offset (drag bucket at C_L>0); "
         "use posy_CD_of_CL (GP-legal, positive coeffs) OR shifted polar. Cruise op-point given.")

# ---- Λ-schedules (fit vs deployment factor μ=cosΛ, exclude μ→0 stowed) ----
def schedule(field, transform=lambda L: np.cos(L * DEG), K=1, kind="ma", label=""):
    Ls, ys = [], []
    for w, v in aero_polar.items():
        L = v["Lam"]; mu = transform(L)
        val = v[field]
        if mu > 1e-6 and val > 1e-9:
            Ls.append(L); ys.append(val)
    order = np.argsort(Ls)
    Ls = np.array(Ls)[order]; ys = np.array(ys)[order]
    mu = transform(Ls)
    if kind == "ma":
        f = monofit(mu, ys)
        f["form"] = f"{label} = {f['c']:.4g} * (cosΛ)^{f['a']:.3f}"
    else:
        _, f = smafit(mu, ys, K)
    f["Lam_deg"] = Ls.tolist(); f["mu_cosL"] = mu.tolist(); f["y"] = ys.tolist()
    return f

results["AERO_schedule_CLalpha"] = schedule("CLa", label="C_Lα(Λ)")   # prior ∝ cosΛ
results["AERO_schedule_CD0"] = schedule("CD0", label="C_D0(Λ)")
results["AERO_schedule_Cl"] = schedule("Cl_absmax", label="|C_l|(Λ)")

# ===================================================================
# 2. HYDRO — stowed drag polar, V_w (Re) dependence, stowed trim
# ===================================================================
hyd = load("hydro_results.csv")
bywv = defaultdict(list)
for r in hyd:
    if r["status"] not in ("ok", "recovered") or r["C_D"] in ("", "nan"):
        continue
    key = (r["wing"], r["V_w"], r.get("notes", ""))
    bywv[(r["wing"], r["V_w"])].append((float(r["alpha"]), float(r["C_D"]), float(r["C_L"])))

# stowed polar at Vw=5 (Wing0)
def hydro_polar(wing, vw):
    d = sorted(bywv[(wing, str(vw))])
    a = np.array([p[0] for p in d]) * DEG
    CD = np.array([p[1] for p in d]); CL = np.array([p[2] for p in d])
    CD0, k, R2 = linreg(CL ** 2, CD)
    CL0, CLa, R2l = linreg(a, CL)
    return dict(CD0=float(CD0), k=float(k), R2_polar=float(R2), CLa=float(CLa), R2_lift=float(R2l),
                CL_arr=CL.tolist(), CD_arr=CD.tolist(), a_arr=(a / DEG).tolist())

_hs = hydro_polar("Wing0", 5)
results["HYDRO_stowed"] = dict(**_hs,
                               note="stowed wing Λ=90 (Wing0), V_w=5 m/s; "
                                    "C_D0>0 so C_D=C_D0+k_w·C_L² is directly GP-legal")
results["HYDRO_deployed"] = dict(**hydro_polar("Wing90", 5),
                                 note="deployed wing Λ=0 (Wing90), V_w=5 m/s")

# Re-dependence of stowed C_D0: fit C_D0,w(Re) as monomial (skin-friction ∝ Re^-0.2 prior)
LREF = 1.021; NU_W = 1.0e-6
re_pts = {"Vw": [], "Re": [], "CD0": []}
for vw in [2, 5, 10, 15, 20]:
    if ("Wing0", str(vw)) in bywv:
        p = hydro_polar("Wing0", vw)
        re_pts["Vw"].append(vw); re_pts["Re"].append(vw * LREF / NU_W); re_pts["CD0"].append(p["CD0"])
if len(re_pts["Re"]) >= 2:
    m = monofit(re_pts["Re"], re_pts["CD0"])
    m["form"] = f"C_D0,w(Re) = {m['c']:.4g} * Re^{m['a']:.3f}   (skin-friction prior exponent −0.2)"
    m.update(re_pts)
    results["HYDRO_CD0_vs_Re"] = m

# stowed trim: C_L,uw(α) slope from Phase-3 fine-α (Wing0 trim block)
trim = [(float(r["alpha"]), float(r["C_L"])) for r in hyd
        if r["wing"] == "Wing0" and r.get("notes") == "trim_block" and r["C_L"] not in ("", "nan")]
trim += [(float(r["alpha"]), float(r["C_L"])) for r in hyd
         if r["wing"] == "Wing0" and r["V_w"] == "5" and r.get("notes", "") == "" and r["C_L"] not in ("", "nan")]
trim = sorted(set(trim))
if trim:
    a = np.array([t[0] for t in trim]) * DEG; CL = np.array([t[1] for t in trim])
    CL0, CLa_uw, R2 = linreg(a, CL)
    results["HYDRO_stowed_trim"] = dict(C_Lalpha_uw=float(CLa_uw), C_L0=float(CL0), R2=float(R2),
                                        a_arr=(a / DEG).tolist(), CL_arr=CL.tolist(),
                                        note="stowed trim dC_L/dα [1/rad], Wing0 fine-α")

# ===================================================================
# 3. CAVITATION — suction peak −C_p,min(C_L)
# ===================================================================
cav = load("cavitation_results.csv")
# pair each cav run with C_L from hydro at matching (wing, alpha, Vw)
clmap = {}
for r in hyd:
    if r["C_L"] not in ("", "nan"):
        clmap[(r["wing"], r["alpha"], r["V_w"])] = float(r["C_L"])
cav_pts = {"CL": [], "negCp": [], "wing": [], "alpha": [], "Vw": []}
for r in cav:
    if r["status"] != "ok":
        continue
    cl = clmap.get((r["wing"], r["alpha"], r["V_w"]))
    negcp = float(r["negCp_min"])
    cav_pts["negCp"].append(negcp); cav_pts["wing"].append(r["wing"])
    cav_pts["alpha"].append(float(r["alpha"])); cav_pts["Vw"].append(float(r["V_w"]))
    cav_pts["CL"].append(cl if cl is not None else np.nan)
negcp_arr = np.array(cav_pts["negCp"])
wing_arr = np.array(cav_pts["wing"]); CLv = np.array(cav_pts["CL"])
results["CAVITATION"] = dict(
    negCp_min_max=float(np.max(negcp_arr)),
    negCp_min_range=[float(np.min(negcp_arr)), float(np.max(negcp_arr))],
    note="TWO configs (stowed Wing0 at C_L~0; deployed Wing90 at C_L~0.4) — fit SEPARATELY",
    **cav_pts)

# --- split by configuration (the two visible trends) ---
for cfg, wname, label in [("stowed", "Wing0", "stowed underwater cruise (GP gate)"),
                          ("deployed", "Wing90", "deployed (reference)")]:
    m = wing_arr == wname
    ncp = negcp_arr[m]; cl = CLv[m]
    entry = dict(config=label, negCp_mean=float(np.mean(ncp)),
                 negCp_max=float(np.max(ncp)), negCp_min=float(np.min(ncp)),
                 CL_range=[float(np.nanmin(cl)), float(np.nanmax(cl))],
                 CL=cl.tolist(), negCp=ncp.tolist())
    good = ~np.isnan(cl) & (cl > 1e-4)
    if good.sum() >= 4 and cl[good].max() > 0.05:    # only fit vs C_L if C_L spans a real range
        f = monofit(cl[good], ncp[good])             # −C_p,min = c·C_L^a
        entry["fit_form"] = f"−C_p,min = {f['c']:.4g}·C_L^{f['a']:.3f}  (rms {f['rms_log']:.3f})"
        entry["fit"] = f
    else:                                            # stowed: C_L≈0, peak set by body geometry
        entry["fit_form"] = f"−C_p,min ≈ {np.max(ncp):.3f} (constant gate; C_L≈0 at trim)"
        entry["gate_value"] = float(np.max(ncp))
    results[f"CAVITATION_{cfg}"] = entry

# ===================================================================
# save
# ===================================================================
with open(os.path.join(OUT, "fit_results.json"), "w") as f:
    json.dump(results, f, indent=2)

# ---------------- human report ----------------
def line(): print("-" * 66)
print("=" * 66); print("  UAUV CFD → GP FIT RESULTS  (from cfd/database/*.csv)"); print("=" * 66)

print("\n[AERO] per-wing drag polar  C_D = C_D0 + k·C_L²   &   lift slope C_Lα")
print(f"{'wing':7} {'Λ°':>4} {'C_D0':>8} {'k':>7} {'R²pol':>6} {'C_Lα/rad':>9} {'R²lift':>6} {'|C_l|max':>8}")
for w in sorted(aero_polar, key=lambda x: aero_polar[x]["Lam"]):
    v = aero_polar[w]
    print(f"{w:7} {v['Lam']:4d} {v['CD0']:8.5f} {v['k']:7.4f} {v['R2_polar']:6.3f} "
          f"{v['CLa']:9.3f} {v['R2_lift']:6.3f} {v['Cl_absmax']:8.5f}")

print("\n[AERO] DESIGN POINT (deployed, Λ=0, Wing90):")
print(f"   C_D0,a = {dep['CD0']:.5f}   k_a = {dep['k']:.4f}   C_Lα,a = {dep['CLa']:.3f} /rad")

print("\n[AERO] Λ-schedules (monomial in cosΛ):")
for key in ["AERO_schedule_CLalpha", "AERO_schedule_CD0", "AERO_schedule_Cl"]:
    r = results[key]
    print(f"   {r.get('form','?')}   (rms_log={r.get('rms_log',float('nan')):.4f})")

print("\n[HYDRO] stowed polar (Λ=90, Wing0, V_w=5):")
h = results["HYDRO_stowed"]
print(f"   C_D0,w = {h['CD0']:.5f}   k_w = {h['k']:.4f}   R²={h['R2_polar']:.3f}   C_Lα,w={h['CLa']:.3f}/rad")
if "HYDRO_CD0_vs_Re" in results:
    print(f"   {results['HYDRO_CD0_vs_Re']['form']}   (rms_log={results['HYDRO_CD0_vs_Re']['rms_log']:.4f})")
if "HYDRO_stowed_trim" in results:
    t = results["HYDRO_stowed_trim"]
    print(f"   stowed trim: dC_L/dα = {t['C_Lalpha_uw']:.3f}/rad   R²={t['R2']:.3f}   (n={len(t['a_arr'])})")

print("\n[CAVITATION] suction peak (split by configuration):")
for cfg in ["CAVITATION_stowed", "CAVITATION_deployed"]:
    e = results[cfg]
    print(f"   {e['config']:32}: C_L∈[{e['CL_range'][0]:.3f},{e['CL_range'][1]:.3f}]  "
          f"−C_p,min∈[{e['negCp_min']:.3f},{e['negCp_max']:.3f}]")
    print(f"      → {e['fit_form']}")

print("\nsaved → gp_build/fits/fit_results.json")
