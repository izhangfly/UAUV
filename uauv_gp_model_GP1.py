#!/usr/bin/env python3
"""
UAUV oblique-wing trans-medium vehicle — Layer-A geometric-programming sizing model.

Transcribed from gp_model.tex (Secs. 4-onwards) in the style of the authors' EPQ
aircraft GP model. CFD-fitted coefficients come from gp_build/fits/fit_results.json
(cfd/database/*.csv). The buoyancy imbalance ξ is SWEPT as a parameter, so the model
is a pure GP at each ξ (gp_model.tex §sec:buoyancy). Water-entry (a_peak) is EXCLUDED
from the GP and applied as a separate post-hoc survival check (see entry_check()).

Objective: maximize payload  ==  minimize m_pay^{-1}   (gp_model.tex Eq. objective).

Usage:
    from uauv_gp_model import build_model, entry_check
    m = build_model(xi=0.15); sol = m.solve(verbosity=0)
"""
import numpy as np
from gpkit import Variable, Model

# reference-unit constants (=1) to keep empirical monomial fits dimensionally clean
SREF, MREF = 1.0, 1.0


def build_model(xi=0.15, V_a=50.0, V_w=10.0, R_a_km=20.0, R_w_km=2.0,
                depth=10.0, objective="payload"):
    """Build the UAUV sizing GP for a given buoyancy imbalance ξ (fixed per solve)."""
    xi = float(xi)

    # ======================= CONSTANTS (SI, unit-checked) =======================
    # -- environment / fluids --
    rho_a = Variable("\\rho_a", 1.225, "kg/m^3", "air density", constant=True)
    rho_w = Variable("\\rho_w", 1000.0, "kg/m^3", "water density", constant=True)
    g     = Variable("g", 9.81, "m/s^2", "gravity", constant=True)
    patm  = Variable("p_{atm}", 101325.0, "Pa", "atmospheric pressure", constant=True)
    pv    = Variable("p_v", 2340.0, "Pa", "water vapour pressure (20C)", constant=True)

    # -- fixed geometry (from CAD, gp_model.tex Table geom) --
    S     = Variable("S", 0.075, "m^2", "wing planform (reference) area", constant=True)
    Sstow = Variable("S_{stow}", 0.075, "m^2", "stowed-wing area", constant=True)
    Swet  = Variable("S_{wet}", 0.42, "m^2", "wetted area", constant=True)
    dhull = Variable("d", 0.10, "m", "hull diameter", constant=True)
    Lhull = Variable("L", 1.021, "m", "hull length", constant=True)
    vol   = Variable("\\nabla", 0.0052, "m^3", "displaced hull volume", constant=True)

    # -- mission / speeds (design requirements) --
    Va = Variable("V_a", V_a, "m/s", "aerial cruise speed", constant=True)
    Vw_req = Variable("V_{w,req}", V_w, "m/s", "required underwater sprint speed", constant=True)
    # available cavitation head p_atm + ρ_w g h − p_v (single monomial: keeps the gate GP-legal)
    p_avail = Variable("p_{avail}", 101325.0 + 1000.0 * 9.81 * depth - 2340.0, "Pa",
                       "cavitation-available pressure at depth", constant=True)
    Ra = Variable("R_a", R_a_km * 1e3, "m", "required aerial range", constant=True)
    Rw = Variable("R_w", R_w_km * 1e3, "m", "required underwater range", constant=True)
    h  = Variable("h", depth, "m", "operating depth", constant=True)

    # -- efficiencies / energy --
    eta_a = Variable("\\eta_a", 0.70, "-", "aerial motor*prop efficiency", constant=True)
    eta_w = Variable("\\eta_w", 0.81, "-", "underwater QPC*motor", constant=True)
    e_b   = Variable("e_b", 5.40e5, "J/kg", "battery specific energy (150 Wh/kg Li-ion)", constant=True)

    # -- structure (Al 6061-T6) --
    sig_y  = Variable("\\sigma_y", 250e6, "Pa", "yield stress", constant=True)
    E_mod  = Variable("E", 69e9, "Pa", "Young's modulus", constant=True)
    rho_m  = Variable("\\rho_m", 2700.0, "kg/m^3", "hull material density", constant=True)
    SF     = Variable("SF", 2.0, "-", "buckling safety factor", constant=True)
    m_fins = Variable("m_{fins}", 0.10, "kg", "fin mass", constant=True)
    m_piv  = Variable("m_{pivot}", 0.25, "kg", "pivot+actuator mass", constant=True)
    m_fix  = Variable("m_{fixed}", 0.30, "kg", "avionics/fixed mass", constant=True)

    # -- CFD-fitted coefficients (gp_build/fitted_coefficients.md) --
    kA_aero = Variable("k'_a", 0.55, "-", "aerial operating-range drag: C_D=k'*C_L^2 (fit)", constant=True)
    CD0w    = Variable("C_{D0,w}", 0.0332, "-", "stowed zero-lift drag (CFD)", constant=True)
    k_w     = Variable("k_w", 21.3, "-", "stowed induced factor (CFD)", constant=True)
    CLa_uw  = Variable("C_{L\\alpha,uw}", 0.053, "1/rad", "stowed trim lift slope (CFD)", constant=True)
    negCpm  = Variable("-C_{p,min}", 1.16, "-", "cavitation suction peak (CFD, stowed gate)", constant=True)
    CLmax   = Variable("C_{L,max}", 0.60, "-", "aerial stall lift ceiling (CFD)", constant=True)

    Sr = Variable("S_r", SREF, "m^2", "area reference (=1)", constant=True)
    Mr = Variable("M_r", MREF, "kg", "mass reference (=1)", constant=True)

    # =============================== FREE VARIABLES ===============================
    m      = Variable("m", "kg", "vehicle mass")
    m_pay  = Variable("m_{pay}", "kg", "payload mass")
    m_b    = Variable("m_b", "kg", "battery mass")
    m_s    = Variable("m_s", "kg", "structural mass")
    m_skin = Variable("m_{skin}", "kg", "hull skin mass")
    t_s    = Variable("t_s", "m", "hull wall thickness")

    CLa    = Variable("C_{L,a}", "-", "aerial lift coefficient")
    CDa    = Variable("C_{D,a}", "-", "aerial drag coefficient")
    Da     = Variable("D_a", "N", "aerial drag")
    Pa     = Variable("P_a", "W", "aerial cruise power")

    Vw     = Variable("V_w", "m/s", "underwater cruise speed (cavitation-bounded)")
    CLuw   = Variable("C_{L,uw}", "-", "stowed trim lift coefficient")
    CDw    = Variable("C_{D,w}", "-", "underwater drag coefficient")
    Dw     = Variable("D_w", "N", "underwater drag")
    Pw     = Variable("P_w", "W", "underwater cruise power")
    Ltr    = Variable("L_{tr}", "N", "trim lift force")
    B      = Variable("B", "N", "buoyancy force")
    Eb     = Variable("E_b", "J", "battery energy")

    con = []

    # ---- Aerial cruise: lift = weight, drag polar, power (gp_model.tex Eqs 1-3) ----
    con += [
        m * g <= 0.5 * rho_a * Va**2 * S * CLa,          # deployed lift >= weight
        CLa <= CLmax,                                     # stall ceiling
        CDa >= kA_aero * CLa**2,                          # operating-range polar (CFD)
        Da  >= 0.5 * rho_a * Va**2 * S * CDa,
        Pa  >= Da * Va / eta_a,
    ]

    # ---- Underwater: buoyancy + ξ trim, stowed polar, power (gp_model.tex §buoyancy) ----
    con += [
        B == rho_w * g * vol,
        Vw >= Vw_req,                                      # meet the sprint-speed requirement
        m * g <= B * (1 + max(xi, 0.0)),                   # weight <= buoyancy(1+ξ) (heavy side)
        Ltr >= max(xi, 1e-4) * B,                          # trim lift closes the vertical balance
        Ltr <= 0.5 * rho_w * Vw**2 * Sstow * CLuw,         # ...supplied by the stowed wing
        CDw >= CD0w + k_w * CLuw**2,                        # stowed underwater polar (CFD)
        Dw  >= 0.5 * rho_w * Vw**2 * S * CDw,               # C_D,w referenced to Aref=S (as in CFD)
        Pw  >= Dw * Vw / eta_w,
    ]

    # ---- Cavitation gate (gp_model.tex §cavitation): −C_p,min ≤ σ, upper-bounds V_w ----
    con += [0.5 * rho_w * Vw**2 * negCpm <= p_avail]

    # ---- Energy / battery (gp_model.tex §propulsion-endurance) ----
    con += [
        Eb >= Pa * (Ra / Va) + Pw * (Rw / Vw),            # energy for both legs
        m_b >= Eb / e_b,
    ]

    # ---- Pressure-hull structure: hoop stress + buckling (gp_model.tex §structure) ----
    p_d = rho_w * g * h                                    # design external pressure
    con += [
        t_s >= p_d * dhull / (2 * sig_y),                 # hoop-stress gauge (monomial)
        # Windenburg-Trilling elastic buckling (monomial): p_cr = 2.42 E (t/d)^2.5 (d/L)  >= SF p_d
        SF * p_d <= 2.42 * E_mod * (t_s / dhull)**2.5 * (dhull / Lhull),
        m_skin >= rho_m * np.pi * dhull * Lhull * t_s,     # thin-tube skin mass
        m_s >= m_skin + m_fins + m_piv,
    ]

    # ---- Mass build-up + payload closure (gp_model.tex §mass) ----
    con += [
        m >= m_pay + m_s + m_b + m_fix,
    ]

    obj = m_pay**-1 if objective == "payload" else m       # maximize payload
    return Model(obj, con)


def entry_check(V_entry=58.0, theta_deg=45.0, m_kg=5.0, d=0.10,
                C=None, a=2.0, b=2.0, c=-1.0, a_max_g=20.0):
    """Post-hoc water-entry survival check (NOT in the GP).
    a_peak = C * (V*sinθ)^a * d^b * m_eff^c ;  m_eff = m + m_a (added mass ~3%).
    C is the CFD-fitted constant (pending the entry DOE); prior exponents (2,2,-1)."""
    if C is None:
        return {"status": "pending", "note": "C awaits entry DOE; exponents prior (2,2,-1)"}
    Vn = V_entry * np.sin(np.radians(theta_deg))
    m_eff = m_kg * 1.03
    a_peak = C * Vn**a * d**b * m_eff**c
    return {"a_peak_g": a_peak / 9.81, "survives": a_peak / 9.81 <= a_max_g,
            "V_n": Vn, "m_eff": m_eff}


def _v(sol, k):
    x = sol(k); return float(x.magnitude) if hasattr(x, "magnitude") else float(x)


if __name__ == "__main__":
    print("=== UAUV Layer-A GP: payload vs buoyancy imbalance ξ ===")
    print("    V_a=50, V_w=10 m/s, R_a=20 km, R_w=2 km, depth=10 m\n")
    print(f"{'xi':>6} {'payload':>8} {'m':>6} {'m_b':>6} {'m_s':>6} {'C_L,a':>6} "
          f"{'C_D,a':>6} {'P_a':>6} {'P_w':>6} {'t_s':>7}")
    for xi in [-0.05, 0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        try:
            m = build_model(xi=xi)
            s = m.solve(verbosity=0)
            print(f"{xi:6.2f} {_v(s,'m_{pay}'):8.3f} {_v(s,'m'):6.2f} {_v(s,'m_b'):6.3f} "
                  f"{_v(s,'m_s'):6.3f} {_v(s,'C_{L,a}'):6.3f} {_v(s,'C_{D,a}'):6.4f} "
                  f"{_v(s,'P_a'):6.0f} {_v(s,'P_w'):6.1f} {_v(s,'t_s')*1e3:6.2f}mm")
        except Exception as ex:
            print(f"{xi:6.2f}  {type(ex).__name__}: {str(ex)[:55]}")
    print("\nEntry survival (post-hoc, not in GP):", entry_check())
