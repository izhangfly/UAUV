# Canonical Nomenclature -- HAUV GP Sizing Model

> **Authoritative symbol table for the Layer-A geometric program.**
> Every symbol has exactly one meaning. Conflicts from the extraction agents (G1--G8)
> are quarantined in the clash map (Section 7); they do **not** enter the GP namespace.
>
> **Date:** 2026-08-02
> **Scope:** gpkit implementation of `/Users/ianzhang/UAUV/gp_model.tex` + extraction files
> `/Users/ianzhang/UAUV/gp_build/extractions/G1.md` through `G8.md`.

---

## 1. Vehicle Geometry

| Symbol | Meaning | Units | GP class | Source / Notes |
|---|---|---|---|---|
| `L` | Hull overall length | m | variable or fixed param | CAD NBody.stl: 1.021 m |
| `d` | Hull maximum diameter | m | variable or fixed param | CAD: 0.100 m; fuselage = body of revolution |
| `f` | Fineness ratio `L/d` | -- | monomial | `f = L/d`; baseline ~10 |
| `S` | Wing planform area (deployed) | m^2 | variable | Reference for all aero coefficients |
| `b` | Wing span (deployed, tip-to-tip) | m | variable | `b^2 = AR * S` |
| `c` | Wing mean chord | m | variable | `c = b / AR` for rectangular wing |
| `AR` | Wing aspect ratio | -- | monomial | `AR = b^2 / S`; deployed ~3.3--7.5 |
| `delta` | Wing overhang per side (stowed) | m | variable | Overhang beyond hull radius; stowed lifting surface half-width. NOT Hoerner dihedral, NOT hydrofoil thickness, NOT flap deflection. |
| `S_wet` | Hull wetted area | m^2 | monomial | `S_wet ~ 2.3 * L * d` (Renilson E-3) or `~ 0.75 * pi * d * L` (Hoerner E-4) |
| `S_front` | Hull frontal area | m^2 | monomial | `S_front = pi * d^2 / 4` |
| `nabla` | Displaced hull volume | m^3 | monomial | `nabla_V` in code (nabla alone = del operator). CAD-derived or `C_pris * pi * d^2 * L / 4` |
| `A_prop` | Propeller disk area | m^2 | monomial | `A_prop = pi * D_prop^2 / 4` |
| `D_prop` | Propeller diameter | m | variable | |
| `t_skin` | Hull shell (skin) thickness | m | variable | THE structural gauge variable. NOT `h` (that is G6 structhull's symbol; see clash map). |
| `t_wing` | Wing skin thickness (or `t/c`) | m | variable | For structural mass / buckling |
| `l_rec` | Dorsal recess length | m | param | ~500 mm from CAD |

---

## 2. Fluid Properties

| Symbol | Meaning | Units / Value | GP class | Source / Notes |
|---|---|---|---|---|
| `rho_a` | Density of air | 1.225 kg/m^3 | fixed constant | Ma et al. Table 1; std. atmosphere 15 C |
| `rho_w` | Density of water | 998.2 kg/m^3 (fresh) / 1025 (sea) | fixed constant | Ma et al. Table 1; 20 C fresh water |
| `mu_a` | Dynamic viscosity of air | 1.789e-5 Pa.s | fixed constant | Ma et al. Table 1 |
| `mu_w` | Dynamic viscosity of water | 1.003e-3 Pa.s | fixed constant | Ma et al. Table 1; use `nu_w = mu_w / rho_w` for Re |
| `nu_w` | Kinematic viscosity of water | ~1.0e-6 m^2/s | fixed constant | `nu_w = mu_w / rho_w` |
| `g` | Gravitational acceleration | 9.81 m/s^2 | fixed constant | |
| `p_atm` | Atmospheric pressure | 101325 Pa | fixed constant | |
| `p_v` | Vapour pressure of water | ~2340 Pa (20 C) | fixed constant | Steam table; ~1710 Pa at 15 C. Brennen E-7 |
| `c_sound_a` | Speed of sound in air | 343 m/s | fixed constant | M < 0.15 incompressible |
| `c_sound_w` | Speed of sound in water | ~1480 m/s | fixed constant | Incompressible at 20 m/s |
| `sigma_y` | Material yield stress | Pa | fixed constant | HY-80: 575.7 MPa; Al 6061-T6: ~276 MPa |
| `E_mat` | Material Young's modulus | Pa | fixed constant | HY-80: 206.8 GPa; Al: ~69 GPa |
| `rho_mat` | Material density | kg/m^3 | fixed constant | Steel: 7850; Al: ~2700 |
| `nu_poisson` | Poisson ratio | -- (0.3 steel) | fixed constant | |

---

## 3. Force and Moment Coefficients

**Critical labeling:** roll coefficient is **lower-case `l`** (letter ell), NOT numeral 1.
Read `C_l` as "C-sub-ell" (roll moment coefficient).

| Symbol | Meaning | GP class | Source / Notes |
|---|---|---|---|
| `C_L` | Lift coefficient (3-D, on reference area S) | variable (fit input) | Aero: deployed wing; hydro: stowed overhang or fins |
| `C_L,a` | Aerial cruise lift coefficient | variable | `C_L` in air at deployed skew |
| `C_L,uw` | Underwater lift coefficient (stowed wing) | variable | `C_L` in water at stowed skew |
| `C_D` | Total drag coefficient | variable (posynomial output) | `C_D = C_D0 + k_ind * C_L^2` |
| `C_D,a` | Aerial drag coefficient | variable | |
| `C_D,w` | Underwater drag coefficient | variable | |
| `C_D0` | Zero-lift drag coefficient | variable (fit output) | Hull + wing profile at zero lift |
| `C_D0( Lambda )` | Zero-lift drag as function of skew | fit output | From aero CFD sweep alpha x Lambda |
| `k_ind` | Induced-drag factor | variable (fit output) | `k_ind = 1 / (pi * e * AR)`; NOT the form factor `(1+k)` |
| `e` | Oswald (span) efficiency factor | variable (fit output) | ~0.8--0.95 for clean wing |
| `C_Dp` | Profile drag coefficient | fit output (posynomial) | `C_Dp(C_L, Re, Lambda)` -- fitted from CFD or XFOIL-like data |
| `C_Lalpha` | Lift-curve slope `dC_L / dalpha` | /rad | fit output | `C_Lalpha(Lambda)` = main aero CFD deliverable |
| `C_l` | **Roll** moment coefficient (lower-case ell) | fit output | `C_l(Lambda)` -- highest-value unknown; NOT numeral one (1). |
| `C_m` | Pitch moment coefficient | fit output | About vehicle CG |
| `C_h` | **Hinge** moment coefficient | fit output | Wing pivot hinge; feeds actuator sizing |
| `C_f` | Skin-friction coefficient | monomial / fit | `C_f = a * Re^(-b)` power-law fit of ITTC'57 line |
| `C_p` | Pressure coefficient | variable (CFD) | `C_p = (p - p_inf) / (0.5 * rho * V^2)` |
| `C_p,min` | Minimum pressure coefficient (suction peak) | fit output | NEGATIVE number for attached flow; `-C_p,min` is the positive suction-peak magnitude |
| `C_D,front` | Drag coefficient on frontal area | variable | `C_D,front = C_D * S / S_front` |
| `C_D,wet` | Drag coefficient on wetted area | variable | `C_D,wet = C_D * S / S_wet` |
| `C_D,entry` | Entry-phase drag coefficient | fit output | Song2020's `c_D`; feeds a_peak monomial |
| `C_x0` | Cavitator drag at zero cavitation number | 0.82 (disk) | fixed constant | Logvinovich 1972; for supercavitating sprint branch only |
| `C_pris` | Prismatic coefficient | -- | fixed param | `C_pris = nabla / (S_front * L)`; ~0.6 for fine fuselage |

---

## 4. Skew, Mission, and Mass

| Symbol | Meaning | Units | GP class | Source / Notes |
|---|---|---|---|---|
| `Lambda` | Wing skew angle | deg or rad | **commanded variable** | `0` = deployed (perpendicular to flow, air cruise); `90` = stowed (parallel to hull, underwater). Matches sweep convention where 0 = unswept. CAD mapping: `WingXX` where `Lambda = 90 - XX`. |
| `V_a` | Aerial cruise speed | m/s | variable | Design spec: 50 m/s |
| `V_w` | Underwater cruise speed | m/s | variable | Design spec: 20 m/s (sprint) or lower cruise |
| `V_entry` | Water-entry speed | m/s | param / sweep | ~54--60 m/s at entry |
| `alpha` | Angle of attack | rad | sweep param | CFD sweep variable; NOT the GP decision variable |
| `gamma_entry` | Entry flight-path angle | deg | param | ~15--25 deg below horizontal |
| `R_a` | Aerial range | m | constraint target | Design spec: 10--30 km |
| `R_w` | Underwater range | m | constraint target | Sprint or cruise range |
| `t_a` | Aerial phase duration | s | variable | `t_a = R_a / V_a` |
| `t_w` | Underwater phase duration | s | variable | `t_w = R_w / V_w` |
| `m` | Total vehicle mass | kg | **objective-linked variable** | |
| `W` | Total vehicle weight `m * g` | N | monomial | |
| `m_pay` | Payload mass | kg | **maximization target** | Objective = `min m_pay^(-1)` |
| `m_b` | Battery mass | kg | variable | Connected to energy via `e_batt` |
| `m_s` | Structure mass (hull + wing + fins) | kg | variable | Posynomial buildup from skin thickness |
| `m_prop` | Propulsion system mass | kg | variable | `m_prop = c_m * P_max` (power-law monomial) |
| `m_fixed` | Fixed mass (avionics, wiring, etc.) | kg | fixed param | |
| `B` | Buoyancy force | N | monomial | `B = rho_w * g * nabla` |
| `xi` | Buoyancy-weight imbalance fraction | -- | **swept parameter** | `xi = (W - B) / B`. Positive = heavy (wing lifts up); negative = buoyant; swept to trace payload--trim frontier. |
| `P_a` | Aerial propulsion power | W | monomial | `P_a = D_a * V_a / eta` |
| `P_w` | Underwater propulsion power | W | monomial | `P_w = D_w * V_w / eta` |
| `P_max` | Maximum electrical power | W | variable | For motor sizing |
| `P_hotel` | Hotel (avionics/systems) power | W | fixed param | ~35--220 W per AUV calibration |
| `P_payload` | Payload power draw | W | fixed param | |
| `E_batt` | Total onboard battery energy | Wh or J | monomial | `E_batt = e_batt * m_b` |
| `e_batt` | Battery system-level specific energy | Wh/kg | fixed param | 100--180 Wh/kg for Li-ion (system level, incl. BMS + packaging); NOT cell-level 250--300 |
| `eta` | Lumped propulsive-chain efficiency | -- | fixed param or posynomial | `eta = eta_prop * eta_motor * eta_ctrl`. ~0.42 lumped (the project design notes 0.50 x 0.85); ~0.81 prop alone (Allen/REMUS) |
| `eta_prop` | Propeller open-water efficiency | -- | fixed param | ~0.81 at design J (Allen QPC); ~0.50 marine prop in air off-design |
| `eta_motor` | Motor efficiency | -- | fixed param | ~0.85 brushless DC |
| `a_peak` | Peak water-entry deceleration | m/s^2 or g | **fit output (monomial)** | `a_peak = C * V_entry^a * d^b * m^c` with expected exponents (2, 2, -1) per Song2020 |

---

## 5. Dimensionless Groups

**Note on `(1+k)`:** The parentheses are Hoerner's own convention -- the form factor
is the quantity `(1+k)`, NOT `1+k` where `k` is an isolated parameter. In this model
`k` alone is reserved for the induced-drag factor `k_ind`. The form factor is always
written as the compound symbol `(1+k)`.

| Symbol | Meaning | Formula / GP class | Source / Notes |
|---|---|---|---|
| `Re` | Reynolds number | `Re = rho * V * L_char / mu` (monomial) | Characteristic length = hull L for body drag, wing c for wing Re |
| `Re_L` | Hull-length Reynolds number | `Re_L = rho * V * L / mu` | Aero ~3.4e6, hydro ~2.0e7 |
| `Re_c` | Chord Reynolds number | `Re_c = rho * V * c / mu` | For wing section polars |
| `sigma` | Cavitation number | `sigma = (p_inf - p_v) / (0.5 * rho_w * V_w^2)` (posynomial LHS) | Surface: ~0.50 at 20 m/s; 10 m depth: ~0.99 |
| `sigma_i` | Incipient cavitation number | `sigma_i = -C_p,min` (CFD-fit constraint) | The GP constraint: `-C_p,min <= sigma` |
| `(1+k)` | Form factor (viscous pressure-drag multiplier) | `(1+k) = 1 + xi_form * (L/d)^(-1.7)` (Renilson E-6, posynomial) OR `= 1 + 1.5*(d/L)^(1.5) + 7*(d/L)^3` (Hoerner E-3, posynomial) | The PARENTHESES carry meaning -- this IS the symbol, not `k` alone. For our hull `(1+k) ~~ 1.05` (bare Hoerner) to 1.12 (Renilson PMB). Baseline: 1.1--1.2 appendage-inclusive. |
| `xi_form` | Form-factor constant | `3` (teardrop), `6` (PMB hull) | param | Renilson Table 1 |
| `k_axial` | Axial added-mass factor | `m_a,axial = k_axial * rho_w * nabla` (monomial for fixed fineness) | ~0.03 for f=10 (Lamb/Newman Fig 4.8) |
| `k_lateral` | Lateral added-mass factor | `m_a,lateral = k_lateral * rho_w * nabla` | ~0.95 for f=10 |
| `k_pitch` | Pitch added-moment-of-inertia factor | `I_a,pitch = k_pitch * rho_w * nabla * L^2` | ~0.9+ for f=10 |
| `M` | Mach number | `M = V / c_sound` | ~0.15 air; incompressible water |
| `Fn` | Froude number (length) | `Fn = V / sqrt(g * L)` | ~6.3 water at 20 m/s; far above displacement regime |

---

## 6. Skew Convention Cross-Reference

The project uses **three** numbering systems for the same physical angle.
This table is the single source of truth.

| System | Deployed (air cruise) | Stowed (water) | Convention |
|---|---|---|---|
| **GP `Lambda`** (THIS TABLE) | 0 deg | 90 deg | Skew angle from deployed; `0 = perpendicular to flow` |
| CAD `WingXX` | `Wing90` | `Wing0` | Angle between span and body (90 = perpendicular) |
| Pipeline `Lambda_pipeline` | 90 | 0 | `Lambda_pipeline = 90 - WingXX` |

**Usage rule:** In equations, text, and gpkit code, use `Lambda` = 0 (deployed) to 90 (stowed).
The CAD mapping is an implementation detail of the STL export script only.

---

## 7. Per-Source Clash Map

Every clash flagged by the extraction agents, with resolution.

| Agent | Source file | Source's symbol | Source's meaning | **OUR canonical** | Resolution |
|---|---|---|---|---|---|
| G6 | structhull | `h` | Shell plating **thickness** | `t_skin` | structhull's `h` is NOT depth; it is the "t" in `sigma = p*a/h`. Renamed to avoid collision with depth `h_depth` everywhere else. |
| G6 | structhull | `a` | Shell mean **radius** | `d/2` or `R` | structhull's `a` is NOT acceleration. Use `d/2` directly or `R` in structural equations only. |
| G6 | structhull | `L` | Frame spacing between stiffeners | `L_bay` (if needed) | Our hull is unstiffened; `L` = hull length takes priority. |
| G4 | Newman | `k_1` | Axial added-mass factor (Lamb) | `k_axial` | Collision with `k_ind` (induced-drag factor). Lamb's `k_1, k_2, k'` become `k_axial, k_lateral, k_pitch`. |
| G4 | Newman | `k_2` | Lateral added-mass factor (Lamb) | `k_lateral` | Same rename. |
| G4 | Newman | `k'` | Pitch added-MoI factor (Lamb) | `k_pitch` | Same rename. |
| G4 | Newman | `m_11` | Axial added mass (dimensional) [kg] | `m_a,axial` | `m_11` is the dimensional coefficient; `k_axial = m_11 / (rho * nabla)`. Use `m_a,axial = k_axial * rho_w * nabla`. |
| G4 | Newman | `m_22 = m_33` | Lateral added mass | `m_a,lateral` | |
| G4 | Newman | `m_55 = m_66` | Pitch/yaw added MoI | `I_a,pitch` | |
| G4 | Newman | `b` | Spheroid equatorial radius | `d/2` | Newman's `b` (spheroid semi-axis) is NOT our wing span `b`. Keep spheroid geometry local to the added-mass derivation only. |
| G4 | Newman | `a` | Spheroid semi-length | `L/2` | NOT acceleration `a`. |
| G4 | Fossen | `M_A` | Added-mass 6x6 matrix | `M_A` | OK as-is in trajectory context; not in GP. |
| G2 | Hoerner (Lift) | `Gamma` | **Dihedral** angle | N/A (quarantined) | Hoerner's capital Gamma = V-tail/dihedral angle, NOT our skew Lambda. Do not import. The `cos^2 Gamma` law is analog only. |
| G2 | Hoerner (Lift) | `tau` | Lift-slope constant (approx. pi) | N/A (drop) | Not needed; use `2*pi` directly. |
| G2 | Hoerner (Lift) | `A` (OCR-mangled to `Lambda`) | Aspect ratio | `AR` | In E-8 text: "dC_L,3D/dalpha = a_O **Lambda**/(A+1+...)" -- the bold Lambda is OCR-mangled **A** (aspect ratio). Always read Hoerner `A` = aspect ratio in context; our `Lambda` = skew only. |
| G2 | dronestube (Si) | `delta` | **Sweep** angle | `Lambda` | Their sweep `delta` (0 = loiter/deployed) = our `Lambda`. Do NOT confuse with our `delta` = wing overhang. |
| G2 | morphing (Chen) | sweep `0 deg` | Deployed | `Lambda = 0` | Convention match confirmed. |
| G3 | Hoerner (Drag) | `C_Dwet` | Drag on wetted area | `C_D,wet` | Keep subscript distinction from frontal-area `C_D`. |
| G3 | Hoerner (Drag) | `C_D,frontal` / `C_Ds` | Drag on frontal area | `C_D,front` | |
| G3 | Hoerner (Drag) | `d/l` | Diameter / length ratio | `d/L` | Same as our `1/f` (inverse fineness). |
| G3 | Renilson | `C_P` | **Form** (pressure) drag coefficient | `C_Pf` | Collision with `C_p` (pressure coefficient) AND `C_pris` (prismatic coefficient). Rename: `C_Pf` = form-drag coefficient. |
| G3 | Renilson / Molland | `C_P` (roman P) | **Prismatic** coefficient | `C_pris` | Separate from `C_p` (pressure) and `C_Pf` (form drag). |
| G3 | Renilson | `K_P` | Form-drag multiplier | `K_form` | `K_form = C_Pf / C_f`. Avoid `K_P` to keep `P` for power. |
| G3 | Renilson | `xi_hull` | Hull form-factor constant | `xi_form` | Renamed to avoid collision with `xi` = buoyancy imbalance. |
| G5 | Brennen | `sigma` | Cavitation number | `sigma` | OK. Collision with structural stress resolved: `sigma` = cavitation number; hoop stress = `sigma_h`; yield stress = `sigma_y`. |
| G5 | Brennen | `sigma_i` | Incipient cavitation number | `sigma_i` | OK. |
| G5 | Brennen | `d` | Cavity half-width | N/A (quarantined) | Brennen's Ch.8 cavity `d` is NOT our hull diameter. Local to cavity theory only. |
| G5 | Amromin | `delta` | Hydrofoil thickness | N/A (quarantined) | NOT our wing overhang `delta`. |
| G5 | Zou | `sigma` | Incipient supercavitation number | `sigma` (same definition) | OK. |
| G7 | southampton (Rutherford) | `Spe` / `S_bar_pe` | Specific energy | `e_batt` | `e_batt` is the canonical symbol; `Spe = e_batt`. The overbar form `\bar{S}_{pe}` is a typesetting variant of the same concept. |
| G7 | southampton | `SpeM_E` | Total onboard energy | `E_batt` | `E_batt = e_batt * m_b`. |
| G7 | southampton | `M_E` | Battery mass | `m_b` | |
| G7 | southampton | `eta_PT` | Lumped power-train efficiency | `eta` | Our chain splits into `eta_prop * eta_motor * eta_ctrl`. |
| G7 | southampton | `C_D,nabla` | Volumetric drag coefficient | N/A (not used) | We use frontal-area convention throughout. |
| G7 | fcauv / sizing2019 | `P` | Power ratio `P_max/P_base` | `P_ratio` (if needed) | Collision with power `P`. Rename to `P_ratio` if hybrid sizing is added. |
| G7 | Allen (REMUS) | `c_d` | Frontal-area drag coefficient | `C_D,front` | Lower-case `c_d` = our `C_D,front`. |
| G7 | Allen (REMUS) | `QPC` | Quasi-propulsive coefficient | `eta_prop` | `QPC` = propeller efficiency = our `eta_prop`. |
| G8 | song2020 | `c_D` | Entry drag coefficient | `C_D,entry` | Song2020's lower-case `c_D` = the peak entry-phase drag coefficient. Feeds `a_peak` monomial. |
| G8 | song2020 | `F` | Axial hydrodynamic force during entry | `F_entry` | OK in entry context. |
| G8 | waterexit (Li) | `C_L` | **Rotor** lift coefficient (propeller law) | `C_L,rotor` | NOT wing lift coefficient. `L_r = C_L,rotor * rho * omega_r^2 * D_r^4`. Only relevant if water-exit phase is modeled. |
| G8 | waterexit | `m_11` | Axial added mass | `m_a,axial` | Same as Newman's `m_11`; use our canonical name. |
| G1 | hoburg2014/hoburg2016/berkeley | `k` | Pressure-drag form factor | `k_ind` | Hoburg's `k` in drag polar `C_D0 + k*C_L^2` = our `k_ind = 1/(pi*e*AR)`. NOT the `k` inside `(1+k)` form factor. |
| G1 | hoburg2014/berkeley | `A` | Aspect ratio | `AR` | Hoburg writes `A` for aspect ratio. We use `AR` to avoid collision with coefficient matrices. |
| G1 | hoburg2014/berkeley | `lambda` | Taper ratio `c_tip/c_root` | `lambda` (if wing not rectangular) | ALSO `lambda` = dual Lagrange multiplier in Ch.3. Our wing is rectangular (`lambda=1`); the taper machinery collapses. |
| G1 | hoburg2014/berkeley | `e` | Oswald efficiency | `e` | OK, matches. |
| G1 | hoburg2014/berkeley | `tau` | t/c (thickness-to-chord ratio) | `t_wing/c` or `tau_tc` | Avoid bare `tau` (Hoerner uses it for pi). Use `tau_tc` if wing thickness is a GP variable. |
| G1 | hoburg2014/berkeley | `nu` | Fitted posynomial of lambda | N/A | Berkeley's `nu(lambda)` is a fitting auxiliary; our rectangular wing gives `nu = constant`. |
| G1 | effmdo / gpintro | `c_k` (signomial) | Negative coefficient in signomial | `c_k` (signed) | OK; SP-local. Signomial coefficients may be negative. |
| All | the project design notes + gp_model.tex | `k` | Form factor / induced-drag factor | **RESOLVED**: `k_ind` = induced-drag factor; `(1+k)` = form factor (always with parentheses) | The single most collision-prone symbol. Never use bare `k` alone; always write `k_ind` or the compound `(1+k)`. |
| All | the project design notes + gp_model.tex | `sigma` | Cavitation number vs structural stress | **RESOLVED**: `sigma` = cavitation number; `sigma_h` = hoop stress; `sigma_y` = yield stress | Both uses are standard in their own fields. Use subscript to disambiguate. |
| All | the project design notes | `h` | Operating depth | `h_depth` (if needed) | Avoid bare `h` (G6 structhull uses it for thickness). Write `p_d = rho_w * g * h_depth` or use `H` for depth. |
| All | the project design notes + gp_model.tex | `e_b` | Battery specific energy | `e_batt` | Renamed from `e_b` to `e_batt` for clarity. |

---

## 8. Symbols from Other Sources NOT Imported

These appear in the extractions but are quarantined (not needed for this model,
or properly belong to another domain).

| Symbol | Source | Reason for exclusion |
|---|---|---|
| `lambda` (dual) | berkeley Ch.3 | Lagrange multipliers; internal to the solver, not a design variable. |
| `nu_i` (dual weights) | berkeley Ch.3 | Probability-like dual variables; solver-internal. |
| `s_i` (slacks) | effmdo/gpintro | SP slack variables; solver-internal. |
| `alpha` (softness param) | hoburg2016data | gpfit fitting parameter; offline, not in the sizing GP. |
| `beta` (all uses) | berkeley/gpintro | SP iteration parameters; solver-internal. |
| `C_D,wave` | gpintro | Wave drag; transonic regime, not relevant at M=0.15. |
| `M_crit` | gpintro | Critical Mach; not relevant. |
| `Delta_p_C` | Brennen | Liquid tensile strength correction to sigma_i; dropped per the project design notes justification (Re >= 1e7, sigma_i ~ -C_p,min). |
| `D_sigma` | Amromin | Inception gap; becomes negligible at Re ~ 1e7 (our regime). |
| `delta` (hydrofoil thickness) | Amromin | Quarantined; our `delta` = wing overhang. |
| `d` (cavity half-width) | Brennen Ch.8 | Quarantined; our `d` = hull diameter. |
| All stiffener symbols (`A_f, h_f, h_w, f, I_c, I_z, ...`) | structhull | Our hull is unstiffened thin tube. Keep only if ring-stiffened variant explored. |
| `DoH` (degree of hybridisation) | fcauv/sizing2019 | Battery-only vehicle; no fuel cell hybrid. |
| `P_fc, m_H2, m_O2` | fcauv | Fuel-cell specific; not in battery-only baseline. |
| `C_L,rotor` (water-exit rotor lift) | waterexit | Only if water-exit phase is explicitly modeled. |
| `C_D,nabla` (volumetric drag) | southampton | We use frontal-area convention. |
| `C_S, C_B` (wetted-surface / block coefficients) | Molland | Ship-specific form parameters; not needed for slender torpedo hull. |
| `n, theta` (nose index, tail semi-angle) | Myring / Gao / Vardhan | Shape parameters for CAD/mesh; fixed in baseline geometry, not GP variables. |
| `y+, u_tau, tau_w` | Gao/Vardhan | CFD mesh parameters; not in GP. |
| `n` (buckling lobe number) | structhull | Discrete integer minimization; baked into fitted monomial offline. |
| `m` (axial half-wave number) | structhull | Same; not in GP. |
| `C_0` (OOC imperfection) | structhull | Out-of-circularity; parameter in buckling fit, not GP variable. |
| `SF` (partial safety factors) | structhull | Baked into constraint constants; not a GP variable. |

---

## 9. Quick-Reference: Most Collision-Prone Symbols

These 5 symbols deserve special caution when reading any source or writing GP code:

1. **`k`** -- "What kind of k?" Always write `k_ind` (induced drag), or `(1+k)` (form factor with parentheses), or `k_axial` / `k_lateral` / `k_pitch` (added mass). Never bare `k`.
2. **`sigma`** -- Cavitation number (default). If structural stress, write `sigma_h` (hoop) or `sigma_y` (yield).
3. **`delta`** -- Wing overhang per side (canonical). Quarantine: sweep angle (dronestube Si), hydrofoil thickness (Amromin), flap deflection (general aero), Kronecker delta (Newman).
4. **`C_p`** -- Pressure coefficient (default). If prismatic, write `C_pris`. If form-drag coefficient (Renilson), write `C_Pf`.
5. **`h`** / **`a`** -- Depth (`h_depth` or `H`) and acceleration (`a`). Quarantine G6 structhull's `h`=thickness (`t_skin`) and `a`=radius (`d/2`).

---

## References (sources whose symbols are reconciled above)

1. Hoerner, S.F. & Borst, H.V. *Fluid-Dynamic Lift*, 2nd ed., 1985.
2. Hoerner, S.F. *Fluid-Dynamic Drag*, 2nd ed., 1965.
3. Newman, J.N. *Marine Hydrodynamics*, 40th anniversary ed., MIT Press, 2018.
4. Fossen, T.I. *Handbook of Marine Craft Hydrodynamics and Motion Control*, Wiley, 2011.
5. Brennen, C.E. *Cavitation and Bubble Dynamics*, Cambridge, 2014.
6. Renilson, M. *Submarine Hydrodynamics*, 2nd ed., Springer, 2018.
7. Rutherford, K.T. *AUV Design Considering Energy Source Selection and Hydrodynamics*, EngD thesis, Southampton, 2008.
8. Chiche, A. et al. "A Strategy for Sizing and Optimizing the Energy System on Long-Range AUVs," IEEE J. Oceanic Eng. 46(4), 2021.
9. Allen, B. et al. "Propulsion System Performance Enhancements on REMUS AUVs," OCEANS 2000.
10. Lin, Z. et al. "Review of Energy Technologies for UUVs," Energies 19, 592, 2026.
11. Song, Z.J. et al. "Experimental and numerical study of the water entry of projectiles at high oblique entry speed," ~2020.
12. Shi, F. et al. "Numerical simulation on the high-speed oblique water entry of twin vehicles," 2026.
13. Si, P. et al. "Tube-Launched UAV with a Variable-Sweep Wing," Drones 8, 474, 2024.
14. Chen, Q. et al. "Morphing aircraft wing variable-sweep: two practical methods," Acta Aerodynamica Sinica 30(5), 2012.
15. Myring, D.F. "A Theoretical Study of Body Drag in Subcritical Axisymmetric Flow," Aeronautical Quarterly 27(3), 1976.
16. Gao, T. et al. "Hull shape optimization for AUVs using CFD," Eng. Appl. Comp. Fluid Mech. 10(1), 2016.
17. Vardhan, H. et al. "Sample-Efficient and Surrogate-Based Design Optimization of Underwater Vehicle Hulls," arXiv:2304.12420, 2023.
18. Molland, A.F. et al. *Ship Resistance and Propulsion*, CUP, 2011.
19. Beatty, T.D. "A Theoretical Method for the Analysis and Design of Axisymmetric Bodies," NASA CR, 1975.
20. Hoburg, W. & Abbeel, P. "Geometric Programming for Aircraft Design Optimization," AIAA J. 52(11), 2014.
21. Hoburg, W. et al. "Data Fitting with GP-Compatible Softmax Functions," Opt. Eng. 17(4), 2016.
22. Boyd, S. et al. "A Tutorial on Geometric Programming," Opt. Eng. 8(1), 2007.
23. Hoburg, W. "Aircraft Design Optimization as a Geometric Program," PhD thesis, UC Berkeley, 2015.
24. York, M.A. et al. "Efficient Aircraft MDO and Sensitivity Analysis via Signomial Programming," AIAA J., 2018.
25. Kirschen, P.G. et al. "Application of Signomial Programming to Aircraft Design," J. Aircraft 55(3), 2018.
26. Dzielski, J. & Kurdila, A. "A Benchmark Control Problem for Supercavitating Vehicles," J. Vibration and Control 9(7), 2003.
27. Zou, W. et al. "Optimized design of the overall shapes of supercavitating vehicles," 2023.
28. Amromin, E. & Rozhdestvensky, K. "Correlation between Pressure Minima and Cavitation Inception Numbers," JMSE 10(7), 2022.
29. Ma, Z. et al. "Configuration Design and Trans-Media Control Status of HAUVs," ~2022.
30. Li, Z. et al. "Water-exit dynamics and system identification for a HAUV," 2025.
31. Shinoka, T.K.L. & Netto, T.A. "Structural Optimization Applied to Submarine Pressure Hulls," J. Ocean Eng. Marine Energy, 2025.
32. Yan, L. et al. "Design and Analysis of a Novel HAUV with Foldable Wings," Drones 8, 669, 2024.
