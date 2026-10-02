#!/usr/bin/env python3
"""
UAUV Layer-A GP — v2: FREE GEOMETRY (bounded) + roll & static-stability gates.

Extends the fixed-geometry GP_1 (see uauv_gp_model_GP1.py, kept immutable). The hull
(d, L), displaced volume, wing (b, c, S) and cruciform fins (area, arm) are now design
VARIABLES bounded by a launch-envelope; drag scales analytically with the geometry
(Hoerner form factor + turbulent skin friction), so it stays valid off the CFD point.
The CFD fits calibrate the stowed polar, cavitation gate, and stall ceiling.

New feasibility gates (gp_model.tex §roll, §stability):
  * roll authority : cruciform fins must out-roll the skew-induced wing moment
  * static stability: horizontal/vertical tail-volume coefficients V_H, V_V >= minimums

Water-entry stays a post-hoc check. ξ swept => pure GP.
Run:  python3 uauv_gp_model.py
"""
import numpy as np
from gpkit import Variable, Model


def build_model(xi=0.15, V_a=50.0, V_w=10.0, R_a_km=20.0, R_w_km=2.0, depth=10.0):
    xi = float(xi)
    # ============================ CONSTANTS (SI) ============================
    rho_a = Variable("\\rho_a", 1.225, "kg/m^3", "air density", constant=True)
    rho_w = Variable("\\rho_w", 1000.0, "kg/m^3", "water density", constant=True)
    mu_a  = Variable("\\mu_a", 1.789e-5, "Pa*s", "air viscosity", constant=True)
    mu_w  = Variable("\\mu_w", 1.0e-3, "Pa*s", "water viscosity", constant=True)
    g     = Variable("g", 9.81, "m/s^2", "gravity", constant=True)

    Va = Variable("V_a", V_a, "m/s", "aerial cruise speed", constant=True)
    Vwr= Variable("V_{w,req}", V_w, "m/s", "required underwater speed", constant=True)
    Ra = Variable("R_a", R_a_km*1e3, "m", "aerial range", constant=True)
    Rw = Variable("R_w", R_w_km*1e3, "m", "underwater range", constant=True)
    h  = Variable("h", depth, "m", "operating depth", constant=True)
    p_avail = Variable("p_{avail}", 101325.0 + 1000.0*9.81*depth - 2340.0, "Pa",
                       "cavitation-available head", constant=True)

    eta_a = Variable("\\eta_a", 0.70, "-", "aerial efficiency", constant=True)
    eta_w = Variable("\\eta_w", 0.81, "-", "underwater efficiency", constant=True)
    e_b   = Variable("e_b", 5.40e5, "J/kg", "battery specific energy", constant=True)

    # design-envelope bounds
    d_lo = Variable("d_{lo}", 0.08, "m", constant=True); d_hi = Variable("d_{hi}", 0.12, "m", constant=True)
    L_lo = Variable("L_{lo}", 0.90, "m", constant=True); L_hi = Variable("L_{hi}", 1.30, "m", constant=True)
    gap  = Variable("gap", 0.30, "m", "span = L - 0.30 m limit (the project design notes)", constant=True)
    Cp_v = Variable("C_p^{\\nabla}", 0.62, "-", "hull prismatic (volume) coeff", constant=True)

    # aero / hydro
    e_os  = Variable("e", 0.85, "-", "Oswald efficiency (analytic prior)", constant=True)
    CDp_a = Variable("C_{Dp,a}", 0.010, "-", "wing section profile drag (NACA3612 min)", constant=True)
    CLmax = Variable("C_{L,max}", 0.60, "-", "aerial stall ceiling (CFD)", constant=True)
    k_w   = Variable("k_w", 21.3, "-", "stowed trim induced factor (CFD)", constant=True)
    negCp = Variable("-C_{p,min}", 1.16, "-", "cavitation suction peak (CFD)", constant=True)

    # structure / masses
    sig_y = Variable("\\sigma_y", 250e6, "Pa", "yield stress (Al)", constant=True)
    E_mod = Variable("E", 69e9, "Pa", "modulus (Al)", constant=True)
    rho_m = Variable("\\rho_m", 2700.0, "kg/m^3", "hull density", constant=True)
    rho_fin = Variable("\\rho_{fin}", 6.0, "kg/m^2", "fin areal mass", constant=True)
    SF    = Variable("SF", 2.0, "-", "buckling SF", constant=True)
    m_piv = Variable("m_{pivot}", 0.25, "kg", "pivot+actuator", constant=True)
    m_fix = Variable("m_{fixed}", 0.30, "kg", "avionics", constant=True)

    # stability / roll gates
    VH_min = Variable("V_{H,min}", 0.40, "-", "min horizontal tail volume", constant=True)
    VV_min = Variable("V_{V,min}", 0.02, "-", "min vertical tail volume", constant=True)
    Cl_dist= Variable("C_{l,dist}", 0.0026, "-", "peak skew-induced wing roll (CFD)", constant=True)
    CLa_fin= Variable("C_{L\\alpha,fin}", 2.5, "1/rad", "fin lift slope (low-AR)", constant=True)
    dmax_f = Variable("\\delta_{max}", 0.35, "rad", "max fin deflection (20 deg)", constant=True)

    # ============================ FREE VARIABLES ============================
    d = Variable("d", "m", "hull diameter"); L = Variable("L", "m", "hull length")
    vol = Variable("\\nabla", "m^3", "displaced volume")
    b = Variable("b", "m", "wing span"); c = Variable("c", "m", "wing chord")
    S = Variable("S", "m^2", "wing area"); AR = Variable("AR", "-", "wing aspect ratio")
    Swet = Variable("S_{wet}", "m^2", "wetted area")
    t_s = Variable("t_s", "m", "hull wall thickness")
    Sfin = Variable("S_{fin}", "m^2", "total fin area"); lfin = Variable("l_{fin}", "m", "fin moment arm")

    m = Variable("m", "kg"); m_pay = Variable("m_{pay}", "kg"); m_b = Variable("m_b", "kg")
    m_s = Variable("m_s", "kg"); m_skin = Variable("m_{skin}", "kg"); m_fins = Variable("m_{fins}", "kg")

    Re_a = Variable("Re_a", "-"); Cf_a = Variable("C_{f,a}", "-"); ff = Variable("(1+k)", "-")
    CLa = Variable("C_{L,a}", "-"); CDa = Variable("C_{D,a}", "-"); CD0a = Variable("C_{D0,a}", "-")
    Da = Variable("D_a", "N"); Pa = Variable("P_a", "W")
    Vw = Variable("V_w", "m/s"); CLuw = Variable("C_{L,uw}", "-"); CDw = Variable("C_{D,w}", "-")
    CD0w = Variable("C_{D0,w}", "-"); Cf_w = Variable("C_{f,w}", "-"); Re_w = Variable("Re_w", "-")
    Dw = Variable("D_w", "N"); Pw = Variable("P_w", "W"); Ltr = Variable("L_{tr}", "N")
    B = Variable("B", "N"); Eb = Variable("E_b", "J")

    con = []

    # ---- GEOMETRY (free, bounded) ----
    con += [
        d >= d_lo, d <= d_hi, L >= L_lo, L <= L_hi,
        vol == Cp_v * (np.pi/4) * d**2 * L,          # displaced volume of the hull
        S == b * c, AR == b/c,                        # wing planform
        b + gap <= L,                                 # span <= L - 0.30 m
        Swet >= np.pi*d*L*0.9 + 2*S,                  # hull + wing wetted area
    ]

    # ---- AERIAL cruise (analytic drag scales with geometry) ----
    con += [
        Re_a == rho_a * Va * c / mu_a,
        Cf_a >= 0.074 / Re_a**0.2,                    # turbulent skin friction (monomial)
        ff >= 1 + 1.5*(d/L)**1.5 + 7*(d/L)**3,        # Hoerner form factor (posynomial)
        CD0a >= Cf_a * ff * Swet/S,                   # zero-lift drag
        CDa >= CLa**2/(np.pi*e_os*AR) + CD0a + CDp_a, # full aerial polar
        m*g <= 0.5*rho_a*Va**2*S*CLa,                 # lift >= weight
        CLa <= CLmax,                                 # stall ceiling
        Da >= 0.5*rho_a*Va**2*S*CDa,
        Pa >= Da*Va/eta_a,
    ]

    # ---- UNDERWATER cruise + buoyancy ξ-trim ----
    con += [
        B == rho_w*g*vol,
        Vw >= Vwr,
        m*g <= B*(1 + max(xi, 0.0)),
        Ltr >= max(xi, 1e-4)*B,
        Ltr <= 0.5*rho_w*Vw**2*S*CLuw,
        Re_w == rho_w*Vw*L/mu_w,
        Cf_w >= 0.074/Re_w**0.2,
        CD0w >= Cf_w*ff*Swet/S,                       # stowed zero-lift drag (analytic, geometry-scaled)
        CDw >= CD0w + k_w*CLuw**2,
        Dw >= 0.5*rho_w*Vw**2*S*CDw,
        Pw >= Dw*Vw/eta_w,
        0.5*rho_w*Vw**2*negCp <= p_avail,             # cavitation gate
    ]

    # ---- ROLL authority gate (gp_model.tex §roll) ----
    # cruciform fins (span ~ fin reach) must supply >= peak skew-induced wing roll moment
    con += [Cl_dist <= CLa_fin*dmax_f*(Sfin/S)*(b/L)]   # fin roll coeff >= disturbance

    # ---- STATIC-STABILITY gates: tail-volume coefficients (gp_model.tex §stability) ----
    con += [
        Sfin*lfin >= VH_min*S*c,                      # horizontal-plane V_H >= min
        Sfin*lfin >= VV_min*S*b,                      # vertical-plane V_V >= min
        lfin <= 0.45*L,                               # tail-fin moment arm (CG-to-tail)
    ]

    # ---- ENERGY / battery ----
    con += [Eb >= Pa*(Ra/Va) + Pw*(Rw/Vw), m_b >= Eb/e_b]

    # ---- STRUCTURE + mass ----
    p_d = rho_w*g*h
    con += [
        t_s >= p_d*d/(2*sig_y),                       # hoop stress
        SF*p_d <= 2.42*E_mod*(t_s/d)**2.5*(d/L),      # Windenburg-Trilling buckling (monomial)
        m_skin >= rho_m*np.pi*d*L*t_s,
        m_fins >= rho_fin*Sfin,
        m_s >= m_skin + m_fins + m_piv,
        m >= m_pay + m_s + m_b + m_fix,
    ]

    return Model(m_pay**-1, con)


def _v(sol, k):
    x = sol(k); return float(x.magnitude) if hasattr(x, "magnitude") else float(x)


if __name__ == "__main__":
    print("=== UAUV Layer-A GP v2 — FREE geometry + roll/stability gates ===\n")
    print(f"{'xi':>5} {'pay':>6} {'m':>6} {'d':>6} {'L':>6} {'b':>6} {'S':>7} {'AR':>5} "
          f"{'S_fin':>7} {'m_b':>6} {'m_s':>6} {'C_L,a':>6} {'t_s':>6}")
    for xi in [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        try:
            s = build_model(xi=xi).solve(verbosity=0)
            print(f"{xi:5.2f} {_v(s,'m_{pay}'):6.3f} {_v(s,'m'):6.2f} {_v(s,'d'):6.3f} "
                  f"{_v(s,'L'):6.3f} {_v(s,'b'):6.3f} {_v(s,'S'):7.4f} {_v(s,'AR'):5.2f} "
                  f"{_v(s,'S_{fin}')*1e4:6.1f}cm2 {_v(s,'m_b'):5.2f} {_v(s,'m_s'):5.2f} "
                  f"{_v(s,'C_{L,a}'):6.3f} {_v(s,'t_s')*1e3:4.2f}mm")
        except Exception as ex:
            print(f"{xi:5.2f}  {type(ex).__name__}: {str(ex)[:52]}")
