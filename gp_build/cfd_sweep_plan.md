# UAUV GP Sizing Model -- CFD Sweep Specification

> **Document status:** definitive. This is the contract between the GP sizing model and the CFD
> campaigns. It defines exactly what to run, over which ranges, what each run must output, and
> which GP constraint each fitted coefficient closes. Parameter ranges derive from the physics
> extractions in `gp_build/extractions/`; every fitted term is backed by an analytic prior from
> those files. Do not run CFD until this document and the Layer-A GP (in gpkit) agree on the
> output contract.

---

## 0. Quick Reference: What CFD Must Produce

| Fitted coefficient | GP constraint it closes | Campaign | Sweep variables | Analytic prior | Source |
|---|---|---|---|---|---|
| `C_D0(Λ)`, `k(Λ)` | Drag polar `C_D = C_D0 + k C_L^2` | AERO | `α x Λ` | Induced `C_Di = C_L^2/(π e AR)`; skin-friction `C_f = 0.074/Re^0.2` (Hoburg, G1 E-10). Pre-subtract these analytically to isolate `C_D0(Λ)`. | G2 E-3, G3 E-3/6 |
| `C_Lα(Λ)` | Lift constraint `L = 1/2 ρ V^2 S C_L` | AERO | `α x Λ` | `C_Lα ∝ cosΛ` (sweep independence principle, G2 E-6); deployed AR=3.3 slope ~ `2πA/(A+2)` | G2 E-2, E-6 |
| `C_l(Λ)` | Roll-authority gate `|C_l(Λ)| ≤ tail capability` | AERO | `Λ` (assessed at mid-α) | `C_l(Λ) ∝ cos^2Λ` aileron-effectiveness law (G2 E-7). **Highest-value unknown per the project design notes §4.** | G2 E-7 |
| `C_D0,w`, `k_w` | Underwater drag polar | HYDRO | `α x Λ`, plus `V_w` sweep | Same induced/skin-friction decomposition as aero; `C_f` at water Re=2e7 | G3 E-3/4/6 |
| `C_L,uw(α, δ)` | Stowed-wing trim `L_trim = 1/2 ρ_w V_w^2 S_stow C_L,uw` | HYDRO | `α` at `Λ=90` (stowed), plus `Λ=80` (near-stowed) | `dL/dα = 2π q δ^2` self-compensation (G2 E-8, the project design notes §4); `C_Lα = πA/2` for slender body | G2 E-8 |
| `-C_p,min(C_L)` | Cavitation gate `-C_p,min ≤ σ` | HYDRO | `α x V_w x h` (depth) | `σ = (p_atm + ρgh - p_V) / (1/2 ρ V^2)` (G5 E-2); `σ_i = -C_p,min` inception (G5 E-3); `D_σ → 0` at `Re > 1e7` (G5 E-9) -- justifies conservative `σ_i ≈ -C_p,min` at our `Re = 2e7` | G5 E-2/3/9 |
| `a_peak = C V^a d^b m^c` | Entry-survival gate `a_peak ≤ 20g` | ENTRY | `V x θ_entry x m` (2-D rigid) | `a_peak = F/m = c_D (π/8) ρ_w V^2 D^2 / m`, exponents (2,2,-1) (G8 E-9, song2020) | G8 E-9/10 |

---

## 1. AERO Campaign (simpleFoam, k-ω SST, air, 50 m/s)

### 1.1 Physics context

The wing deployed at 50 m/s in air produces the lift that carries the 5 kg vehicle. The drag
polar `C_D = C_D0 + k C_L^2` feeds the aerial-cruise power constraint (gp_model.tex Eqs 3-5;
Hoburg ref. G1 E-7). The lift-curve slope `C_Lα(Λ)` enters the lift constraint `L = 1/2 ρ V^2 S C_L`
(G1 E-7). The roll coefficient `C_l(Λ)` feeds the roll-authority trajectory gate -- the single
highest-value unknown identified in the project design notes §4.

**Analytic decomposition (pre-subtraction).** Per Hoburg (G1 E-10) and the induced-drag law
(G2 E-3), the total drag polar is:

```
C_D = C_D0(Λ) + C_L^2/(π e AR) + (CDA)_0/S        (posynomial)
```

where `C_L^2/(π e AR)` is the induced term (analytic, computable from the known planform and
Oswald `e` fitted from the CFD runs), and `(CDA)_0/S` is the hull/fin parasite drag (analytically
isolated via G3 skin-friction subtraction). The CFD's job is to supply `C_D0(Λ)` and the
effective Oswald `e(Λ)`. Pre-subtract the induced term from each CFD `C_D` value using the
known `A(Λ)` table (see below) and an initial `e ≈ 0.85` estimate, then fit `C_D0(Λ)` and
refine `e(Λ)` iteratively.

The skin-friction coefficient is analytic (power-law, GP-compatible, G1 E-10, G3 E-4):

```
C_f = 0.074 / Re^0.2          (turbulent, Re < 1e7)
```

with `Re_chord = ρ_a V_a c / μ_a ≈ 1.225 × 50 × 0.14 / (1.789e-5) ≈ 4.8e5`.

### 1.2 Meshes (5 wings, bracketing the sweep curve)

The CAD (`~/UAUV/stl/`) supplies 10 wing bodies `Wing0..Wing90` at 10-degree steps, where
`WingXX` = angle between span and body (`90 = deployed, 0 = stowed`). Pipeline skew angle
`Λ = 90 - XX`.

**Select 10 meshes that bracket the curve, with higher density near deployed (where resolution matters for the cruise polar):**

| CAD wing | `Λ` (skew, aero convention) | Purpose | Rationale |
|---|---|---|---|
| `Wing90` | `0` (deployed, perpendicular) | Cruise design point | Baseline polar; the `Λ=0` anchor |
| `Wing80` | `10` | Near-deployed refinement | High-resolution capture of the linear `cosΛ` region; critical for cruise-adjacent off-design |
| `Wing70` | `20` | Near-deployed refinement | Second point in the 0–30° cruise-relevant envelope; resolves curvature before sweep effects intensify |
| `Wing60` | `30` | High-speed sweep | Captures the `cosΛ` region; compare against dronestube `δ=30` (G2 E-12) |
| `Wing50` | `40` | Mid-sweep | Bridges systematic 10° increments; starts to separate linear `cosΛ` from AR-collapse regime |
| `Wing45` | `45` | Mid-sweep bracket | Bracket midpoint (now redundant for 10° spacing but retained for continuity with prior work) |
| `Wing40` | `50` | Mid-sweep | Continues systematic coverage; AR effects become more pronounced |
| `Wing30` | `60` | Dash / high-skew | Near-stowed roll; the AR-collapse transition; compare dronestube `δ=60` |
| `Wing20` | `70` | High-skew refinement | Captures steep AR-drop region; improves fit fidelity near the stowed roll floor |
| `Wing10` | `80` | High-skew refinement | Second point in the steep roll-off; ensures no unexpected behavior between 70–90° |
| `Wing0` | `90` (stowed, parallel) | Stowed roll | AR-collapse floor; `C_l(Λ=90)` calibration for the roll-transient model |

**Full 10° sweep:** The 10 meshes span the entire 0–90° range at uniform 10° increments, with additional retention of `Wing45` (Λ=45) as a legacy midpoint. The 0–30° cruise-relevant region is now refined with three points (Λ=0, 10, 20, 30) for robust gradient and curvature resolution. If the fitted `C_Lα(Λ)` or `C_l(Λ)` shows unexpected kinks in the 30–60° or 60–90° ranges, the uniform 10° spacing already provides sufficient coverage to diagnose them.

**Geometric quantities per Λ** (pre-compute from the STL at each mesh):

| Λ | Projected span (m) | Projected area (m²) | Effective AR `b²/S` |
|---|---|---|---|
| 0 (deployed) | 0.71 | 0.075 | ~6.72 |
| 10 | ~0.69 | ~0.073 | ~6.52 |
| 20 | ~0.65 | ~0.069 | ~6.12 |
| 30 | ~0.61 | ~0.065 | ~5.72 |
| 40 | ~0.56 | ~0.060 | ~5.22 |
| 45 | ~0.50 | ~0.053 | ~4.72 |
| 50 | ~0.46 | ~0.048 | ~4.40 |
| 60 | ~0.36 | ~0.038 | ~3.41 |
| 70 | ~0.25 | ~0.031 | ~2.02 |
| 80 | ~0.14 | ~0.027 | ~0.73 |
| 90 (stowed) | ~0.10 | ~0.025 | ~0.40 |

*Exact values to be computed from the STL; this table uses the CAD measurements from CLUADE.md §4 for the chord=0.14 m, span=0.71 m wing and interpolates/extrapolates the projected quantities at 10° increments.*

### 1.3 Angle-of-attack sweep (α)

**One mesh per Λ; change α by rotating the inlet velocity vector. No remeshing.**

Sweep α from -4 degrees (negative to bracket the zero-lift point) to stall (~12--16 degrees) in
2-degree increments. This yields ~9--11 runs per mesh, ~50 runs total for the AERO campaign.

| α (deg) | α (rad) | Purpose |
|---|---|---|
| -4 | -0.070 | Zero-lift crossing, confirm symmetry |
| -2 | -0.035 | Pre-stall linear region |
| 0 | 0 | Zero-AoA baseline |
| 2 | 0.035 | Low cruise CL bracket |
| 4 | 0.070 | Nominal cruise CL |
| 6 | 0.105 | |
| 8 | 0.140 | |
| 10 | 0.175 | Expected `C_L,max` vicinity |
| 12 | 0.209 | Near stall |
| 14 | 0.244 | Post stall (if attached) |
| 16 | 0.279 | Confirmed stall |

If flow separates fully before 16 degrees, truncate after 2 consecutive α-steps showing
decreasing `C_L`. If still attached at 16 degrees (unlikely at this Re), continue in 2-degree
steps until stall.

**Inlet velocity rotation.** For each α, set the inlet `U` vector:

```
U_x = 50 cos(α),  U_z = 50 sin(α)       (x = axial, z = vertical in body frame)
```

and rotate the `forceCoeffs` `liftDir` and `dragDir` accordingly:

```
liftDir  = (-sin α, 0, cos α)      // perpendicular to freestream
dragDir  = ( cos α, 0, sin α)      // parallel to freestream
```

### 1.4 What each run must output

Parse `postProcessing/forceCoeffs/0/coefficient.dat`. For each (Λ, α) point record:

1. **`C_L`**, **`C_D`**, **`C_m`** -- mean of the final 10% of iterations; also record the
   standard deviation `std(C_L)`, `std(C_D)` as a convergence quality flag.

2. **`C_l` (roll coefficient) -- this is the single highest-value unknown.** The
   `forceCoeffs/Moment` reports moment about the body x-axis. Compute `C_l = M_x / (q S b)`
   where `q = 1/2 ρ V^2`, using the reference `S` and `b` for the deployed configuration.
   **Note:** `C_l` is near zero at `Λ = 0` (symmetric deployed wing) and grows as the wing
   skews. Its sign depends on the pivot side; record signed values.

3. **Wing-only forces if separable.** If the mesh allows separate force patches for the wing
   vs. the hull+tail, record wing-only `C_Lw`, `C_Dw`, `C_lw`. This enables direct `C_l(Λ)`
   fitting without hull-interference confounding. If patches cannot be cleanly separated (the
   wing-hull junction is a single surface), record total-body coefficients and note the
   interference as a systematic uncertainty.

4. **`μ_t/μ` field check (not averaged -- spot-check only).** For each mesh at `α = 4` degrees,
   export the `mut/mu` field and verify it does not pin at floor (1e-3) or ceiling (1e4) over
   extended regions. This is the the project design notes §6 diagnostic; if it pins, the mesh spacing or `y+`
   needs adjustment.

### 1.5 Fitted outputs and GP targets

From the DOE data, fit the following using gpfit (Hoburg 2016 method, G1 E-14..E-19):

| Fit | GP form | Independent var(s) | gpfit class | Analytic prior |
|---|---|---|---|---|
| `C_D0(Λ)` | Posynomial / SMA | `Λ` (deg or rad) | `C_D0 ≥ f_SMA(Λ)`, relax to inequality | `~constant + small-to-moderate rise from tip separation` (G2 E-17 chen2012morphing) |
| `k(Λ)` = `1/(π e(Λ) AR(Λ))` | Posynomial (via `e(Λ)` fit) | `Λ` | `k ≥ f_SMA(Λ)` | `k = 1/(π e AR)`, `e ≈ 0.8--0.95` decreasing with Λ (G2 E-3) |
| `C_Lα(Λ)` | Posynomial / SMA | `Λ` | `C_Lα ≥ f_SMA(Λ)` | `C_Lα ∝ cosΛ` (G2 E-6); deployed value ~ `2π AR/(AR+2)` ≈ 4.3/rad (G2 E-2) |
| `C_l(Λ)` | Posynomial | `Λ` | `C_l ≥ f_SMA(Λ)` (or signomial if signed) | `C_l(Λ) ≈ C_l(0) · cos^2Λ` (G2 E-7); **CFD-fitted across the factor-of-20 unknown range** |

**Fitting procedure** (Hoburg 2016, G1 E-14/E-19):
1. Log-transform all data `(x = log u, y = log w)`.
2. Screen for log-log convexity (G1 E-25 from Boyd). If affine in log-log, a single monomial suffices.
3. Fit SMA (softmax-affine, G1 E-16) with `K = 2--4` terms, 20 random restarts (G1 E-19); take best RMS log error.
4. Relax equality to inequality `w ≥ f_SMA(u)` (G1 E-5 posynomial-equality relaxation).
5. Verify monotonicity: if the GP objective penalises drag, the relaxation is tight at the optimum.
6. Persist each fit to `gp_build/fits/` as both the gpkit constraint string and the raw fitted parameters.

**ISMA (implicit softmax-affine, G1 E-17) is recommended for `C_D0(Λ)` if the drag-vs-sweep
curve shows a sharp kink (e.g., at the AR-collapse transition near Λ ~ 60 degrees), since ISMA
handles localised sharp features better than SMA at equal K.**

### 1.6 Roll-authority gate (offline, not CFD)

After CFD supplies `C_l(Λ)`, the trajectory sim (step [6] of the project design notes §6) computes:

```
roll rate  ≤  tail authority margin
```

using the roll-damping timescale `τ = 2 I_xx V / (q S b^2 |C_lp|) ≈ 0.10--0.12 s` from
the project design notes §4. This gate is checked in the trajectory sim, not in the GP. The GP carries
`C_l(Λ)` only as a prescribed schedule; the GP does not simulate the transient.

---

## 2. HYDRO Campaign (simpleFoam, water)

### 2.1 Physics context

Underwater at 20 m/s the dynamic pressure is 130x that of air. The wing is stowed (`Λ = 90`),
and the 18 mm overhang `δ` on each side provides a hydrodynamic trim force (the project design notes §4,
G2 E-8). The cavitation constraint `-C_p,min ≤ σ` (G5 E-3) caps the feasible speed-vs-depth
envelope.

The underwater drag polar `C_D,w = C_D0,w + k_w C_L^2` feeds the underwater power constraint
(gp_model.tex Eq. 11). The stowed-wing lift `C_L,uw(α, δ)` feeds the trim constraint
(gp_model.tex Eq. 10). The suction peak `-C_p,min(C_L)` feeds the cavitation gate
(gp_model.tex Eq. 13).

### 2.2 Meshes and angle-of-attack sweep

Use the **same 5 wing meshes** as the AERO campaign (Wing90/60/45/30/0). The mesh geometry is
identical; only the fluid properties, inlet velocity, and solver settings change.

**α sweep per mesh:** same as aero, -4 to stall in 2-degree increments. Underwater stall
behaviour may differ from air (higher Re, different BL development); sweep until stall is
confirmed.

**Stowed-wing trim block (special).** At `Λ = 90` (Wing0) and `Λ = 80` (Wing10), run an
extended α sweep from -8 to +8 degrees in 1-degree increments. The stowed wing's `C_L,uw(α)`
is the trim-force source (gp_model.tex Eq. 10); the fine α resolution captures the
`dL/dα = 2π q δ^2` self-compensation linear regime (G2 E-8) and any nonlinearity at larger α.

### 2.3 Velocity sweep (V_w)

At the **deployed** (Wing90, Λ=0) and **stowed** (Wing0, Λ=90) configurations, sweep `V_w`:

```
V_w = {2, 5, 10, 15, 20} m/s
```

This yields the `C_D,w(V_w)` and `C_Lα,w(V_w)` dependence, capturing any Reynolds-number
effects on the drag polar and stall behaviour across the 2--20 m/s operating range.

At each `(Λ, V_w, α)`, record all force coefficients. The `C_D0,w` fit should be expressed as
a function of `Re` (via the skin-friction power law, G3 E-4) rather than `V_w` directly,
ensuring GP compatibility.

### 2.4 Depth / cavitation-margin sweep

Cavitation number depends on hydrostatic pressure (G5 E-2/E-6):

```
σ = (p_atm + ρ_w g h - p_V) / (1/2 ρ_w V_w^2)
```

Sweep depth `h = {0, 2, 5, 10} m`:

| h (m) | `p_∞` (kPa) | `p_∞ - p_V` (kPa, at 20 degC) | `σ` at `V_w = 20` m/s | `σ` at `V_w = 2` m/s |
|---|---|---|---|---|
| 0 | 101.3 | 99.0 | 0.495 | 49.5 |
| 2 | 121.0 | 118.6 | 0.593 | 59.3 |
| 5 | 150.4 | 148.1 | 0.741 | 74.0 |
| 10 | 199.5 | 197.2 | 0.986 | 98.6 |

Depth does NOT change the pressure field (the flow solution is independent of `p_∞` in
incompressible simpleFoam). **Depth enters ONLY through `σ` after CFD**: at each `(Λ, α, V_w)`
point, extract `C_p,min` from the pressure field, then compute `σ` analytically for each
depth and check `-C_p,min ≤ σ`. Therefore the depth sweep costs ZERO additional CFD runs --
it is a pure post-processing check.

**Run the cavitation check at the stowed-wing (Wing0) + worst case:** highest `V_w = 20` m/s,
highest `α` (within the stowed trim range, up to ~8 degrees), surface depth `h = 0`. If
`-C_p,min < σ` at this point, the entire envelope is cavitation-free and no further checks
are needed. If it approaches or exceeds `σ`, then the `V_w` ceiling is set by cavitation
onset at a specific `(C_L, h)` combination.

### 2.5 What each run must output

Parse `postProcessing/forceCoeffs/0/coefficient.dat` as for AERO. Additionally:

1. **`C_P` field.** Export the full pressure field on wing and hull surfaces. Extract
   `C_p,min = min(C_p)` over all wall patches (the most negative value). Compute
   `-C_p,min(C_L)` by pairing each `C_p,min` with the corresponding `C_L` from the
   forceCoeffs output.

2. **Wing-surface `C_p,min` vs hull-surface `C_p,min`.** If the wing patch is separable,
   record the minimum on the wing alone -- the stowed wing's overhang is the likely cavitation
   inception site. If the propeller hub or fin tips show lower `C_p,min`, note separately.

3. **`μ_t/μ` field** spot-check as for AERO (at `α = 4`, `V_w = 20`).

### 2.6 Fitted outputs and GP targets

| Fit | GP form | Independent var(s) | gpfit class | Analytic prior |
|---|---|---|---|---|
| `C_D0,w` | Posynomial | `Re` (via skin-friction subtraction) | Monomial `C_D0,w ≥ C_f,water (1+k) S_wet/S` | Hoerner (G3 E-3): `(1+k) = 1 + 1.5(d/l)^1.5 + 7(d/l)^3`; Renilson (G3 E-6): `(1+k) = 1 + ξ (L/D)^{-1.7}`, ξ=6 PMB |
| `k_w` | Posynomial / SMA | `Λ` | `k_w ≥ f_SMA(Λ)` | Same form as aero `1/(π e AR)`; use fitted `e_w(Λ)` |
| `C_Lα,uw(α, δ)` | Posynomial / SMA | `α` (stowed, Λ=90) | `C_L,uw ≥ f_SMA(α)` | **dL/dα = 2π q δ^2** (G2 E-8, the project design notes §4); `C_Lα = πA/2` for slender body (G2 E-8 Jones) |
| `-C_p,min(C_L)` | Posynomial / ISMA | `C_L` | `-C_p,min ≥ f_ISMA(C_L)` | Inception `σ_i = -C_p,min` (G5 E-3); `D_σ → 0` at our Re (G5 E-9) |

**Stowed-wing self-compensation check.** After fitting `C_Lα,uw(α)`, compute
`dL/dα = 1/2 ρ_w V_w^2 S_stow · C_Lα,uw` and compare against the analytic
`dL/dα = 2π q_w δ^2` (G2 E-8, the project design notes §4). The agreement or discrepancy is one of the
project's key research findings (Direction 1 in the project design notes §8).

**Cavitation fit: use ISMA (G1 E-17) for `-C_p,min(C_L)`.** The suction peak typically has a
sharp onset near `C_L,max` -- an implicit softmax-affine with per-term `α_k` captures this
local kink better than SMA with a single global softness parameter.

---

## 3. ENTRY Campaign (interFoam VOF, 2-D rigid, cavitation OFF)

### 3.1 Physics context

The peak entry deceleration `a_peak` is the survival gate (the project design notes §4, §7 gate `a_peak ≤ 20g`).
The song2020 water-entry projectile study (G8 E-9) establishes the monomial scaling:

```
a_peak = F/m = c_D (π/8) ρ_w V^2 D^2 / m = C · V^a · d^b · m^c
```

with the analytic prior `(a, b, c) = (2, 2, -1)`. The interFoam DOE fits the constant `C`
(which encodes nose shape, entry angle, and the peak-to-steady `c_D` ratio) and tests whether
the exponents deviate from the theoretical values.

**Cavitation is OFF for v1.** Per the project design notes §5, the entry speed 50--60 m/s is far below
Long et al.'s 150 m/s where the Zwart model was needed. The Amromin `D_σ → 0` result (G5 E-9)
also validates that cavitation effects on entry loads are negligible at our Re.

**2-D rigid body justification.** The vehicle is an axisymmetric slender body (L/D=10). A 2-D
slice through the symmetry plane captures the nose-entry impact -- the peak deceleration occurs
at the instant of nose contact, before 3-D cavity expansion or hull-wetting effects dominate
(G8 E-9, G8 E-10). The 2-D simplification cuts mesh size by ~100x vs 3-D and makes the DOE
tractable. The trade is that 3-D cavity pinch-off and lateral added-mass asymmetry are not
captured; these affect the post-peak trajectory, not the peak magnitude.

### 3.2 Geometry

A 2-D profile of the forward fuselage, taken from the Myring nose of the CAD model (NBody.stl).
The profile extends from the nose tip to at least the mid-body station (`x ≈ 0.5 m`) to ensure
the cavity is fully developed before the domain outlet. The geometry is a single closed curve
extruded one cell thick in the spanwise direction (`empty` front/back patches).

Reference diameter `d = 0.10 m` (hull max diameter).

### 3.3 Variable sweep

| Variable | Values | Purpose | Source |
|---|---|---|---|
| `V_entry` (m/s) | 70, 60, 50, 40, 30 | Dive **accelerates** as the wing stows, so entry speed can exceed cruise; 70 = fast/steep worst case down to 30 = shallow minimum | G8 E-9 |
| `θ_entry` (deg, from horizontal) | -15, -30, -45, -60, -75 | Dive trajectory angles; `-15` = shallow, `-75` = steep near-vertical plunge | the project design notes §4 skew-scheduling table |
| `m` (kg) | 3, 5, 8 | Brackets the ~5 kg design point; `m=3` lightweight/reserve, `m=8` heavy/payload-max | G8 E-9 |

**Total runs: 5 x 5 x 3 = 75** (`cfd/batch_entry_fixed.sh`). Entry angle enters through the
**normal penetration speed** `V_n = V_entry · sin|θ_entry|`, which governs the slam (Wagner
theory; song2020 G8 E-10 finds the tangential component's effect is secondary). Cases collapse
approximately onto `a_peak(V_n)`.

**Domain setup (body-fixed vertical-entry frame — `cfd/entry_template/`):**
- 2-D slice, X-Z plane, 1 cell thick in Y (`empty` front/back). Domain X=±0.5 m, Z=[-0.6, +0.7] m.
- Slender ogive nose (Myring, D=0.10 m, L_n=0.15 m, L_b=0.50 m), **axis vertical (Z)**, tip at Z=0.
- Body is **stationary**; the whole fluid moves **up** at `V_n` (Galilean-equivalent to the body
  descending at `V_n`). The free surface starts at Z=0 (tip just touching) and rises to wet the
  nose. Because the tip is a point (zero area), the t=0 force is ~0 — **no impulsive spike**.
- Gravity `g = -9.81 m/s^2` (-Z). Body deceleration fictitious force neglected during the peak
  (a_body small at the peak instant); `a_peak = F_peak / m` where `m` is the vehicle mass.
- **Per-case `endTime = clamp(0.3 / V_n, 0.004, 0.05) s`** — scales so the peak (nose penetrating
  ~0.3–0.5 diameter) is captured for slow *and* fast entries. A fixed 5 ms would truncate the
  slow/shallow corner (`V=30, θ=-15` → V_n=7.8 m/s → peak near 8 ms).

### 3.4 What each run must output

1. **Acceleration time history** of the body CoM: `a_x(t), a_z(t)` (body-frame or earth-frame,
   clearly labelled). Extract `a_peak = max(|a_vector|)` over the simulation window.
   Report in both m/s^2 and g.

2. **Force time history:** total hydrodynamic force on the body patches `F_x(t), F_z(t)`.
   This validates the `F/m` calculation and separates drag (axial) from lift/slamming (normal).

3. **Phase fraction `α_water`** snapshots at `t = {2, 5, 10, 20} ms` for the first few runs
   to verify the cavity shape, free-surface deformation, and that the domain boundaries are
   far enough.

4. **Peak `C_p`** on the nose tip (optional, for cross-reference with the HYDRO cavitation data).

### 3.5 Fitted output and GP target

| Fit | GP form | Independent var(s) | gpfit class | Analytic prior |
|---|---|---|---|---|
| `a_peak` | Monomial | `V, d, m` (and `θ_entry` if significant) | `a_peak ≥ C · V^a · d^b · m^c` (monomial equality relaxed) | `(a,b,c) = (2,2,-1)` (G8 E-9); `C` encodes nose shape and `c_D,peak` (G8 E-9) |

**Fitting procedure:**
1. Log-transform the DOE data: `log(a_peak_i) = log(C) + a log(V_i) + b log(d_i) + c log(m_i)`.
2. Solve the linear least-squares problem for `(log C, a, b, c)`. This is a single monomial
   fit; no SMA/ISMA is needed if the log-log plot is reasonably affine (Boyd G1 E-25/E-27).
3. Report the fitted exponents with 95% confidence intervals against the theoretical values.
   If `a ≈ 2.0 ± 0.3`, `b ≈ 1.0 ± 0.5`, and `c ≈ -1.0 ± 0.3`, the song2020 law is
   validated for this nose shape.
4. If the entry-angle effect exceeds a factor of 2 over the sweep range, expand the monomial:
   `a_peak = C · V^a · d^b · m^c · (sin θ_entry)^e` (or `θ_entry^e` if positive-valued),
   where `sin θ_entry` captures the added-mass-rate argument (G8 E-10: steeper entry → faster
   added-mass growth → higher peak). Fit `e` from the data.
5. Persist to `gp_build/fits/entry_monomial.json`.

---

## 4. Phase 2: Cavitation Add-On (conditional)

### 4.1 Trigger condition

Run the cavitation check on the stowed-wing HYDRO case at `V_w = 20 m/s, α = 8 deg, h = 0`
(Wing0, worst-case combination of highest speed + highest trim angle + shallowest depth).
If `-C_p,min ≥ σ ≈ 0.5` (i.e., cavitation is predicted at the surface), then:

1. Model cavitation on **only** the stowed-wing (Wing0) case at `V_w ≥ 15 m/s` using the
   Schnerr-Sauer or Zwart-Gerber-Belamri model in interPhaseChangeFoam (or the equivalent
   cavitation-capable simpleFoam variant).

2. Sweep `V_w = {15, 17.5, 20}` m/s and `α = {2, 4, 6, 8}` degrees at `Λ = 90` (stowed).
   This is ~12 additional runs.

3. Re-extract `-C_p,min(C_L)` from the cavitating solution and compare against the
   non-cavitating fit. The difference `Δ(-C_p,min)` is the cavitation correction to the GP
   constraint.

### 4.2 Justification for OFF in v1

- Entry speed (50--60 m/s) is 3x below Long et al.'s 150 m/s where cavitation was modelled
  (the project design notes §5).
- Amromin & Rozhdestvensky (G5 E-9): `D_σ = |min(Cp)| - σ_i → 0` at `Re ≳ 1e7`. Our hull
  `Re = 2e7` in water → `σ_i ≈ -C_p,min` is well-justified.
- The `-C_p,min ≤ σ` constraint (G5 E-3) is conservative -- real inception occurs at `σ` LOWER
  than `-C_p,min` due to tensile strength and residence-time effects (G5 E-4). Using the
  equality as a hard ceiling errs on the safe side.
- The cavitation margin at the expected cruise depth of 2--10 m is substantially larger than
  at the surface (σ = 0.59--0.99 vs 0.50 at 20 m/s). The trim equilibrium likely settles at a
  depth where cavitation is not a concern.

---

## 5. Database and Cache

### 5.1 Persistent evaluation store

Every CFD evaluation is persisted to a CSV file (or SQLite database) before any fitting step.
The schema:

```
campaign | Λ (deg) | α (deg) | V (m/s) | h (m) | m (kg) | θ_entry (deg) |
C_L | C_D | C_m | C_l | C_L_std | C_D_std | C_p_min | a_peak |
iterations | converged | mesh_cells | timestamp | notes
```

- `converged` = True if residuals dropped below tolerance and force coefficients are steady.
  Set `C_L = NaN, C_D = NaN, ...` and `converged = False` on divergence. **Never crash the
  batch.**
- `mesh_cells` = cell count for the grid-convergence tracking.
- Python script `gp_build/parse_coeffs.py` reads `postProcessing/forceCoeffs/0/coefficient.dat`
  and writes the row. This script is the single point of truth for parsing.

### 5.2 Restart logic

Before launching a case, query the database for an existing row with the same design vector.
If found and `converged = True`, skip. If found and `converged = False`, re-run with a
different `fvSolution` relaxation setting (or a finer mesh) and overwrite.

### 5.3 Grid-convergence study

**One dedicated run at the nominal design point:** `Λ = 0` (Wing90), `α = 4 deg`,
`V_a = 50 m/s`, air.

| Mesh | Cell count (approx.) | Purpose |
|---|---|---|
| Coarse | 0.5 M | Fast turnaround |
| Medium | 1 M | Nominal DOE resolution (the project design notes §6: "1--2 M cells with wall functions, y+ 30--300") |
| Fine | 2 M | Richardson-extrapolation pair with Medium |
| Very fine | 4 M | Richardson-extrapolation pair with Fine; asymptotic range check |

Use the same mesh topology (block structure, refinement regions, prism layers) across all 4
meshes; vary only the base cell size. Report the grid uncertainty on `C_D` using Richardson
extrapolation:

```
U_grid = |(C_D,fine - C_D,medium) / (r^p_order - 1)|
```

where `r` is the refinement ratio and `p_order ≈ 2` (nominal second-order discretisation).

Report the grid-convergence result in the final GP documentation, not in this spec.

---

## 6. Summary Table: Every Fitted Coefficient, Its GP Constraint, and Its Prior

| # | Fitted coefficient | GP constraint | Campaign | Independent variables | Analytic prior | Fitting method | Source |
|---|---|---|---|---|---|---|---|
| 1 | `C_D0(Λ)` | `C_D ≥ C_D0 + C_L^2/(πeAR) + C_f(1+k)S_wet/S` | AERO | `Λ` | Pre-subtract `C_Di` and `C_f(1+k)S_wet`; remainder is `C_D0`. Expected ~0.01--0.03 range, rising with Λ (tip separation, G2 E-17) | SMA/ISMA, K=3--4 (G1 E-16/17) | G2 E-3, G3 E-3/6 |
| 2 | `k(Λ)` = `1/(π e(Λ) AR(Λ))` | Same drag polar as #1 | AERO | `Λ` | `k = 1/(π e AR)`; `e ≈ 0.85` deployed, decreasing with Λ | SMA, K=2--3 | G2 E-3 |
| 3 | `C_Lα(Λ)` | `L = 1/2 ρ V^2 S C_L` | AERO | `Λ` | Deployed: `2π AR/(AR+2) ≈ 4.3/rad` (G2 E-2). Stowed: `π AR/2 ≈ 0.16/rad` (G2 E-8). `C_Lα(Λ) ∝ cosΛ` (G2 E-6) | SMA, K=2--3 | G2 E-2/6/8 |
| 4 | `C_l(Λ)` | Roll-authority gate (trajectory sim, not GP) | AERO | `Λ` | `C_l(Λ) ∝ cos^2Λ` (G2 E-7). Near-zero at Λ=0. **Highest-value unknown.** | SMA, K=2--4 (signed: may need signomial) | G2 E-7 |
| 5 | `C_D0,w` | Underwater drag polar | HYDRO | `V_w` (via `Re`) | `C_f,water(1+k) S_wet/S`. `C_f = 0.075/(log_10 Re - 2)^2` (ITTC'57, G3 E-4); `(1+k) = 1 + ξ(L/D)^{-1.7}`, ξ=6 (G3 E-6). C_D,frontal ≈ 0.10 (G3 E-6) | Monomial / fit `a,b` in `C_f = a Re^{-b}` (G3 synthesis) | G3 E-3/4/6 |
| 6 | `k_w` | Underwater drag polar | HYDRO | `Λ` | Same form as #2, with water `e_w(Λ)` | SMA, K=2--3 | G2 E-3, G3 E-3 |
| 7 | `C_L,uw(α)` | `L_trim = 1/2 ρ_w V_w^2 S_stow C_L,uw` | HYDRO | `α` (stowed, Λ=90) | `dL/dα = 2π q_w δ^2` (G2 E-8). For δ=18 mm, q_w=200 kPa: ~784 N/rad (the project design notes §4) | SMA, K=2--3 | G2 E-8 |
| 8 | `-C_p,min(C_L)` | `-C_p,min ≤ σ` cavitation gate | HYDRO | `C_L` | Inception `σ_i = -C_p,min` (G5 E-3); `D_σ → 0` at Re>1e7 (G5 E-9) | ISMA, K=3--4 (sharp onset near stall, G1 E-17) | G5 E-2/3/9 |
| 9 | `a_peak = C V^a d^b m^c` | `a_peak ≤ 20g` entry-survival gate | ENTRY | `V, d, m` (and `θ_entry` if significant) | `(a,b,c) = (2,2,-1)` (G8 E-9 song2020). `C = c_D,peak · π/8`; `c_D,peak` depends on nose shape (G8 E-9) | Monomial (linear least-squares in log space, G1 E-27) | G8 E-9/10 |

**Total CFD runs (nominal):**

| Campaign | Meshes / configs | α-steps per config | Velocity / depth points | Total runs |
|---|---|---|---|---|
| AERO | 5 meshes | ~10 | 1 (V=50 m/s) | ~50 |
| HYDRO (α x Λ) | 5 meshes | ~10 | 1 (V=20 m/s) | ~50 |
| HYDRO (α x V_w) | 2 configs (deployed + stowed) | ~5 | 5 V_w | ~50 |
| HYDRO (stowed trim) | 2 configs (Λ=90 + Λ=80) | ~17 (fine α) | 1 (V=20 m/s) | ~34 |
| ENTRY | 1 profile | N/A (entry speed is the sweep) | 48 (4V x 4θ x 3m) | 48 |
| Grid convergence | 1 config | 1 α | 4 meshes | 4 |
| **Total** | | | | **~236** |

The HYDRO α-sweep at deployed (Λ=0) overlaps with the AERO physical case (same mesh, different
fluid). These runs are NOT shared because the `forceCoeffs` reference area, fluid properties,
and output processing differ. However, the mesh files are reused.

**Restart-safe batch structure:** 236 runs at ~30--60 min each on 6 performance cores (M3 Pro)
= ~20--40 wall-clock hours for the steady-state cases. The ENTRY transient cases are ~2--4 h
each on 2-D = ~200 h worst case; run these last and in parallel (one per core). Total wall time
~1--2 weeks on the author's machine at part-time utilisation.

---

## References (cross-document)

All equation references use the extraction file numbering:

- **G1** -- Hoburg GP machinery & gpfit fitting method (`gp_build/extractions/G1.md`)
- **G2** -- Wing aerodynamics & sweep laws (`gp_build/extractions/G2.md`)
- **G3** -- Hull/body drag & resistance (`gp_build/extractions/G3.md`)
- **G5** -- Cavitation inception & `σ` (`gp_build/extractions/G5.md`)
- **G8** -- Water-entry impact & peak deceleration (`gp_build/extractions/G8.md`)
- **gp_model.tex** -- GP sizing model formulation & CFD requirements table (`~/UAUV/gp_model.tex`)
- **the project design notes** -- Project handoff, physics, and decisions log (`~/UAUV/the project design notes`)
