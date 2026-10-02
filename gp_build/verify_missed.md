# Completeness Audit: Equations Not Yet Captured in the GP Model

**Audit date:** 2026-08-02
**Method:** Systematic search of all 36 .mmd OCR files against 9 topic categories, comparing
findings against the current GP model (`gp_model.tex`) and the 8 extraction files (`G1..G8.md`).

**Overall assessment:** The extraction was thorough. Of ~60 candidate equations found, 6 are
genuinely new and valuable for the GP model. The corpus has no simpler wing-weight monomial,
no Myring-specific wetted-area closed form, and no analytical exit-thrust sizing law beyond
what is already covered. The stability-derivative block (Topic 5) is the richest untapped vein.

---

## 1. Wing Structural Model

**Finding:** Nothing simpler than the Hoburg wing-box model is present in the corpus.

The Hoburg compact wing-weight monomial (G1 E-B-1, Eq. 2.17 constraint 6):
$$W_w = 45.42 S + 8.71\times10^{-5}\frac{N_{\text{lift}} b^3 \sqrt{W_0 W}}{S\tau}$$
is already documented in `G1.md` and consciously de-scoped for this project (the project design notes:
"our stowing wing is a single continuous panel on a central pivot... treat as a rectangular wing").
No AUV/UAV paper in the corpus supplies an alternative wing-mass relation (e.g., mass per unit
span or monomial fit for small UAV wings). The drones papers (Si et al. 2024, Chen/Yan et al.
2024) give wing geometry but no wing-mass equation.

**Verdict: NOTHING USEFUL.** The de-scoping was correct; no simpler alternative exists in the corpus.

---

## 2. Control-Surface / Fin Sizing

### 2a. Hoerner Tail Volume Coefficient (HIGH)

**Source:** Hoerner 1985 (Fluid-Dynamic Lift), Chapter XI "Longitudinal Stability and Control"
**File:** `Fluid-dynamic_lift__Hoerner__1985_text.mmd`, lines 3529-3533
**Equation:**
$$V_H = \frac{S_H}{S}\frac{l_H}{\bar{c}}$$
where $S_H$ = horizontal tail area, $l_H$ = tail moment arm (distance from CG to tail quarter-chord),
$\bar{c}$ = wing mean aerodynamic chord. Hoerner uses this to relate tail pitching moment to
wing moment:
$$C_{L}\frac{\Delta x}{c} = C_{LH}\frac{S_H}{S}\frac{l_H}{c}$$

**GP class:** monomial (if $S_H$, $l_H$ are variables; constants if fixed in the `hybrid' scheme)
**Which block it strengthens:** Roll-authority gate (Sec. 4.11) and stability constraint (not yet present)
**Why missed:** G2 extraction focused only on wing lift/drag/skew; the "Longitudinal Stability"
chapter of Hoerner's *Lift* was not assigned to any extraction agent.
**Why it matters:** The GP model currently treats the cruciform VFin+HFin geometry as fixed
constants. If fin size becomes a design variable, $V_H$ is the canonical monomial that
translates fin area into pitch/roll/yaw authority. For the roll-authority gate
$|C_l(\Lambda)| \le C_{l,\max}$, the $C_{l,\max}$ could be expressed as a function of
fin tail-volume coefficient rather than as an opaque constant.

**Priority: HIGH** -- the single most importable control-surface equation.

### 2b. Control-Surface Lift Effectiveness dC_L/dδ (MEDIUM)

**Source:** Hoerner 1985, Chapter IX "Control Surfaces", Eq. ~1 (line 2717 region)
**Equation (theoretical, 2-D):**
$$\frac{d\alpha}{d\delta} \approx f(c_f/c)$$
and the empirical chart-based values: at $c_f/c = 0.2$ to $0.4$, $d\alpha/d\delta \approx 0.4$ to
$0.67$ (Fig. 2 of the control-surface chapter). The 3-D correction multiplies by the
finite-wing lift-curve slope.

**GP class:** constant (if fin planform is fixed); monomial if chord ratio is variable
**Why missed:** Control-surface chapter was outside the G2 extraction scope (G2 was wing
aerodynamics only).
**Why it matters:** Provides the link between fin deflection angle $\delta_{\text{fin}}$ and
the resulting $C_L$ increment -- needed to translate the $C_{l,\max}$ fin-authority bound
(Eq. in gp_model.tex Sec. 4.11) into a physical fin-angle constraint.

**Priority: MEDIUM** -- needed only if fin deflection enters the GP as a variable.

### 2c. Renilson Appendage Lift-Slope Notation (LOW)

**Source:** Renilson 2018 (Submarine Hydrodynamics), Nomenclature (lines 182-195)
Renilson defines coefficients $C_{L\delta B}$, $C_{L\delta R}$, $C_{L\delta S}$ for bow-plane,
rudder, and stern-plane lift vs deflection, plus flow straightening factors $\gamma_B, \gamma_R, \gamma_S$.
These are defined as symbols in the nomenclature but the empirical equations for computing them
are in the manoeuvring chapter (Ch. 3), which was partially OCR-failed.
**Verdict:** Symbol definitions only; the actual empirical prediction equations were not captured
in the OCR. **NOTHING USEFUL** (without the full Ch. 3 source).

---

## 3. Propeller / Thruster Model

### 3a. Quasi-Propulsive Coefficient Decomposition (HIGH)

**Source:** Renilson 2018, Chapter 5, Eq. 5.4
**File:** `Submarine Hydrodynamics ( PDFDrive ).mmd`, lines 1973-1977
**Equation:**
$$\text{QPC} = \eta_H \cdot \eta_O \cdot \eta_R$$
with $\eta_H = (1-t)/(1-w)$ (Eq. 4.2), where $t$ = thrust deduction fraction, $w$ = Taylor
wake fraction. $\eta_O$ = open-water propeller efficiency, $\eta_R$ = relative rotative
efficiency $\approx 1.05$ for single-propeller submarines (D_prop/D_hull = 0.4-0.7).
Typical QPC range: 0.8-1.0 for submarines.

**GP class:** monomial in the efficiency chain (if efficiencies are constants)
**Which block it strengthens:** Propulsion efficiency chain (Sec. 4.4, Eq. for $\eta_a$)
**Why missed:** G7 extraction captured the REMUS QPC value (0.811) and the actuator-disk
$\eta_i$ from Hoburg E-9, but did not capture this *decomposition* of QPC into
hull/open-water/rotative components.
**Why it matters:** The current GP model uses a lumped $\eta_{\text{prop}} \approx 0.81$ for
underwater. Renilson's decomposition lets us split this into $\eta_O$ (design-dependent,
function of propeller loading $K_T/J^2$) and hull-efficiency factors $(1-t)/(1-w)$ (function
of aft-body shape). This is physics-based and more GP-expressible than a single constant.

**Priority: HIGH** -- enables a propeller-sizing constraint that ties prop diameter, RPM,
and thrust to efficiency.

### 3b. Newman Open-Water Propeller Coefficients K_T, K_Q, J (MEDIUM)

**Source:** Newman 2018 (Marine Hydrodynamics), Chapter 2, Figs 2.9-2.10 + text (lines 382-404)
**Equations (standard, from text):**
$$K_T = \frac{T}{\rho n^2 D^4}, \quad K_Q = \frac{Q}{\rho n^2 D^5}, \quad J = \frac{U_A}{nD}, \quad \eta_O = \frac{J}{2\pi}\frac{K_T}{K_Q}$$
Newman gives the theoretical definition (Eq. 22 for $\eta_O$) and notes $K_T$, $K_Q$ are
decreasing functions of advance ratio $J$, with max $\eta_O$ at small $\alpha$, typical
max 0.6-0.8.

**GP class:** monomials (K_T, K_Q, J are monomials in T, n, D, U_A); $\eta_O$ as a function
of K_T, K_Q is GP-legal if K_T, K_Q are constants or fitted
**Which block it strengthens:** Propulsion efficiency (Sec. 4.4)
**Why missed:** G7 captured the REMUS QPC (0.811) as a fixed value derived from these
coefficients, but did not extract the canonical definitions.
**Why it matters:** These are the standard non-dimensional propeller parameters. If propeller
diameter $D_p$ or RPM $n$ become GP variables, these monomials let us write
$T = K_T \rho n^2 D_p^4$ and constrain $\eta_O$ from the Wageningen B-series or from
CFD-fitted $K_T(J), K_Q(J)$ curves.

**Priority: MEDIUM** -- these are "textbook standard" and could be cited from Newman directly;
the GP model already captures the relevant efficiency value (0.81).

### 3c. Hoburg Actuator-Disk Efficiency (ALREADY COVERED)

Hoburg Eq. 37 (G1 E-9): $\eta_i \le 2/(1+\sqrt{1+T/(\frac12 \rho V^2 A_{\text{prop}})})$ is
already documented and referenced in `gp_model.tex` Sec. 4.4. Nothing new to add.

---

## 4. Neutral-Buoyancy Trim / Hydrostatics

### 4a. Southampton Mass Ratio and Buoyancy-Constrained Sizing (MEDIUM)

**Source:** Rutherford 2008 (Southampton EngD thesis), Chapter 7, Eqs. 7.1-7.6
**File:** `1230769.mmd`, lines 1776-1798
**Key equations:**
$$M_{AUV} = M_{SS} + M_E + M_B \quad \text{(7.1)}$$
$$B = -\nabla_B(\rho_W - \rho_B) \quad \text{(7.2)}$$
$$M_B = \frac{-\rho_B}{(\rho_W-\rho_B)}\left((\nabla_{SS}+\nabla_E)\rho_W - (M_{SS}+M_E)\right) \quad \text{(7.4)}$$
and the Mass Ratio concept: $M_E = \text{Mass Ratio} \times M_{AUV}$, enabling Eq. 7.6 which
solves for $M_{AUV}$ without explicit $M_B$ or $M_E$.

**GP class:** posynomial (the buoyancy-balance mass buildup is posynomial)
**Which block it strengthens:** Mass build-up (Sec. 4.6) and buoyancy trim (Sec. 4.7)
**Why missed:** G7 extraction focused on the energy/endurance equations; the structural
mass-buoyancy coupling equations in Chapter 7 were not extracted.
**Why it matters:** The Mass Ratio concept ($M_E/M_{AUV}$) is a single parameter that
captures the energy-source mass fraction, allowing the buoyancy-constrained sizing loop
to be solved analytically. This is a simpler alternative to the $\xi$-trim sweep for
early-stage sizing, and is backed by real AUV data (Mass Ratio values 0.3-0.8 across
the AUV fleet).

**Priority: MEDIUM** -- the $\xi$-trim approach in the current GP model is more powerful
(parametric sweep over buoyancy fraction), but the Mass Ratio provides a validation
anchor and a simple closed-form alternative.

### 4b. Renilson Prismatic Coefficient and Displacement Types (LOW)

**Source:** Renilson 2018, Nomenclature (lines 1684-1686)
$$C_P = \frac{\nabla}{A_m L}$$
where $A_m$ = midships cross-sectional area. Also distinguishes *hydrostatic displacement*
(excluding free-flood water) from *form displacement* (including it).
**GP class:** monomial (volume constraint)
**Why missed:** These are nomenclature definitions; the equations are already implicit in the
GP model's use of $\nabla$ as displaced volume.
**Verdict: NOTHING USEFUL** -- already implicitly included.

---

## 5. Stability Derivatives (MAJOR FIND)

### 5a. Renilson Vertical and Horizontal Stability Indices (HIGH -- single best find)

**Source:** Renilson 2018, Chapter 3, Eq. 113 + Table 3.8
**File:** `Submarine Hydrodynamics ( PDFDrive ).mmd`, lines 1088-1094, 1362-1363
**Equation:**
$$G_V = 1 - \frac{M'_w (m' + Z'_q)}{M'_q Z'_w}$$
$$G_H = 1 - \frac{N'_v (m' - Y'_v)}{N'_r Y'_v} \quad \text{(by analogy, horizontal plane)}$$
where primes denote non-dimensional derivatives (e.g., $Z'_w = Z_w/(\frac12 \rho V L^2)$).
$G_V > 0$ implies static stability; $G_V = 1$ is neutral (zero manoeuvring margin).

**Acceptable ranges (Table 3.8, from Ray et al. 2008):**
- $G_V$: **0.5--0.8** (high stability required in vertical plane -- broaching/grounding risk)
- $G_H$: **0.2--0.4** (moderate stability; some manoeuvrability desired)

Also provides control effectiveness criteria (fin sizing constraints):
- Stern planes heave effectiveness: 2.5--4.5
- Stern planes pitch effectiveness: 0.2--0.4
- Rudder sway effectiveness: 3.0--5.0

**GP class:** signomial (the $M'_w/(M'_q Z'_w)$ ratio has mixed signs in derivatives; but
$G_V$ itself is a dimensionless constraint $0.5 \le G_V \le 0.8$)
**Which block it strengthens:** NEW -- a stability constraint block that does not currently exist
in the GP model
**Why missed:** The entire stability/manoeuvring content was outside the scope of any
extraction agent. G4 was assigned "added mass & buoyancy" (Newman + Fossen); stability
derivatives in Renilson Ch. 3 were not extracted.
**Why it matters significantly:** The current GP model has NO static stability constraint.
A trans-medium vehicle that is statically unstable in pitch/yaw would be unflyable.
$G_V$ and $G_H$ provide quantitative, GP-expressible stability gates. In the GP, the
hydrodynamic derivatives $Z'_w, M'_w, Z'_q, M'_q$ can be approximated from fin geometry
(using the tail-volume coefficient from Finding 2a above) plus body Munk moment.

**Priority: HIGH** -- this is the single most important block missing from the sizing model.
A vehicle without a static-margin constraint can converge to an unstable optimum.

### 5b. Stability Derivative Framework from Hoerner (MEDIUM)

**Source:** Hoerner 1985, Chapter XI "Longitudinal Stability"
**Equations (text, lines 3521-3533, 3695-3697):**
Stability requires $\frac{dC_m}{dC_L} < 0$ (negative pitching-moment derivative).
Static margin = $(x_{CG} - x_{AC})/c$. Tail contribution:
$$\frac{dC_{mH}}{dC_L} = \frac{dC_{LH}}{d\alpha} \cdot \frac{S_H}{S} \cdot \frac{l_H}{c} \cdot \left(1 - \frac{d\varepsilon}{d\alpha}\right)$$
where $d\varepsilon/d\alpha$ is the downwash derivative at the tail.

**GP class:** posynomial (if geometry terms are monomials and derivatives are fixed constants
or fitted)
**Why missed:** Hoerner's stability chapter was outside extraction scope.
**Why it matters:** Provides the physics for why $G_V$ takes the form it does -- enables
writing the stability constraint directly from fin geometry rather than relying on
hydrodynamic derivative tables.

**Priority: MEDIUM** -- use to derive GP-compatible approximations for $Z'_w, M'_w$, etc.
from geometry, rather than treating them as CFD outputs.

---

## 6. Material / Structural Mass Relations

**Finding: NOTHING USEFUL** in the corpus.

The Southampton thesis (Rutherford 2008) discusses the "building block" modular mass method
and the "weight displacement centres summary" but provides no mass-per-unit-area or
mass-fraction regression equation for hull skins. The submarine design rules it cites
(Burcher & Rydill 1994: "payload volume is 30% of pressure hull volume") are qualitative
rules of thumb, not posynomial mass relations.

The only mass breakdown equation in the corpus is Rutherford's Eq. 7.1
($M_{AUV} = M_{SS} + M_E + M_B$), which is already covered under Topic 4 above.

The corpus contains no empirical regression for AUV structural mass fraction vs displaced
volume, no skin-mass-per-unit-area formula, and no parametric mass model beyond what
the GP model already handles via $m_s \ge m_{\text{skin}} + m_{\text{fins}} + m_{\text{pivot}}$
and the hoop-stress thickness constraint (G6 E-0).

---

## 7. Wetted-Area Formulas

**Finding: ALL ALREADY COVERED.** Two independent wetted-area monomials exist in the corpus,
both extracted in G3:

1. **Hoerner E-4:** $S_{\text{wet}} \approx 0.75 \pi d l$ (constant 0.7-0.8)
2. **Renilson E-3:** $S_{\text{hull}} \approx 2.25 L D$ (agrees to ~5% with Hoerner using 0.72)

There is **no Myring-specific analytical wetted-area formula** in the corpus. Myring (1976),
Gao (2016), and Vardhan (2023) all define the Myring nose/tail shape equations analytically
but compute volume and wetted area by numerical integration, not by a closed-form expression.
This is because the Myring profile is a transcendental function of its parameters (n, $\theta$);
no elementary antiderivative exists for its surface area. The corpus is consistent: all
sources treat Myring wetted area as a numerical (CFD-integrated) quantity.

**Molland** (via Molland & Turnock 2011, preview only) defines $C_S = S/(\nabla L)^{1/2}$
and $S/\nabla^{2/3}$ as non-dimensional parameters, but the explicit $(1+k)$ derivation
(Ch. 4) was not in the preview. This is covered by Renilson E-6.

**Verdict: NOTHING NEW.** The two canonical monomial forms (Hoerner + Renilson) are sufficient.

---

## 8. Reynolds-Number Correction to Drag

### 8a. Renilson Roughness Allowance (MEDIUM)

**Source:** Renilson 2018, Section 4.8.3.1
**File:** `Submarine Hydrodynamics ( PDFDrive ).mmd`, line 1856
**Value:** $\Delta C_F = +0.0004$ added to the ITTC friction coefficient for hull roughness,
imperfections, and vent holes. Explicitly stated: "For surface ships a value of 0.0004 is
sometimes added."

**GP class:** constant (additive to $C_f$)
**Which block it strengthens:** Hydrodynamic drag build-up (Sec. 4.8)
**Why missed:** G3 extracted the ITTC $C_F$ line and the form factor, but the roughness
allowance constant was noted in passing and not elevated to an equation.
**Why it matters:** The GP model currently uses $f_{\text{SLA}}$ as a dimensionless
service-life-allowance factor multiplying $(1+k)$. Renilson's $+0.0004$ is the standard
marine-engineering form of the same correction, operating on $C_F$ rather than $(1+k)$.
For consistency with marine practice, add this constant rather than (or in addition to)
the SLA factor.

**Priority: MEDIUM** -- small numerical impact ($\sim$1-2% on total drag at our Re).

### 8b. Hoerner Transverse-Curvature C_f Correction (LOW)

**Source:** Hoerner 1965, Chapter II, Eq. 32 (line 1034)
**Equation:**
$$\frac{\Delta C_f}{C_{f0}} = k \frac{l/d}{R_f^m}, \quad \Delta C_f \approx 0.0016 \frac{l/d}{R_f^m}$$
where $k \approx 0.022$--$0.025$, negligible for $l/d=10$ (our case: $\sim$1.5% increment).

**GP class:** monomial in $l/d$ and $R_f^{-m}$ (but $R_f$ involves $C_f$ itself through Re)
**Why missed:** On MISSING_PAGE_FAIL pages in Hoerner drag OCR.
**Why it matters:** Confirms that transverse-curvature correction to $C_f$ is negligible
($\ll 2\%$) for a slender body at $l/d=10$, validating the flat-plate friction assumption.

**Priority: LOW** -- negligible for our geometry.

### 8c. Hoerner Three-Dimensionality / Transition Decrement (LOW)

**Source:** Hoerner 1965, Chapter II, Eq. 31 (line 1028)
$$\Delta C_f = 2/R_d = 2(l/d)/R_l$$
for laminar flow on a cylinder in axial flow. For turbulent flow, effect is even smaller.
Also: the Prandtl transition decrement $\Delta C_f = k/R_l$ with $k=1700$ at critical
$Re \approx 5\times10^5$.

**Verdict: NOTHING USEFUL** for the GP model -- all effects are $\ll 2\%$ at our Re and $l/d$.

---

## 9. Water-Exit Thrust Requirement

### 9a. Propeller/Rotor Thrust Law for Water Exit (MEDIUM)

**Source:** Li et al. 2025 (Water-exit dynamics), Eq. 1
**File:** `Water-exit dynamics and system identification...mmd`, lines 76-83 (G8 E-4)
**Equation:**
$$L_r = C_L \cdot \rho_{\text{air}} \cdot \omega_r^2 \cdot D_r^4$$
with free-space $C_L \approx 0.005$ (measured). Surface-effect amplification: peak
$\bar{C}_L$ at $h/D_r \approx 0.6$--$1.0$, $\sim +20\%$ over free-space value.
Acceleration during exit: $\bar{a}_z$ = 6-19 m/s$^2$ (0.6--1.9 g).

**GP class:** monomial (thrust $\propto \omega_r^2 D_r^4$)
**Which block it strengthens:** Could be added as a water-exit constraint: rotor thrust
must exceed $(mg - B)$ to break the surface
**Why missed:** This is already extracted in G8 E-4. It is NOT currently incorporated
into `gp_model.tex` because the GP model assumes booster launch (not self-powered exit).
**Why it matters:** If the mission concept ever changes to include self-powered water
exit, this monomial provides the exit thrust constraint. The $C_L = 0.005$ constant is for
a 30-inch rotor on a 25.7 kg vehicle -- scaling to our 1 m / 5 kg vehicle needs
re-calibration.

**Priority: MEDIUM** for the current booster-launch concept; would become HIGH if
self-powered exit is added to the mission.

### 9b. Water-Exit Drag Force Data (LOW)

**Source:** Chen/Yan et al. 2024 (Drones 8:669, foldable-wing HAUV)
**File:** `drones-08-00669-v2.mmd`, lines 158-160
**Data:** At 3 m/s exit velocity: max drag force $\approx 75$ N, max pitching moment
$\approx 38$ N$\cdot$m. At 4 m/s: $\approx 130$ N and $\approx 70$ N$\cdot$m.
Vehicle mass 2.5 kg. Drag scales roughly as $V^2$.

**GP class:** data point only (no equation)
**Verdict: NOTHING USEFUL** beyond validation -- qualitative confirmation of $V^2$ scaling.

---

## Summary: Priority-Ranked Findings

| # | Finding | Source | Priority | GP Block | Status |
|---|---|---|---|---|---|
| 1 | **Stability indices $G_V$, $G_H$ + acceptable ranges** | Renilson Eq. 113, Table 3.8 | **HIGH** | NEW (stability gate) | Not in model |
| 2 | **Tail volume coefficient $V_H = (S_H/S)(l_H/c)$** | Hoerner 1985, Ch. XI | **HIGH** | Roll-authority gate (Sec. 4.11) | Not in model |
| 3 | **QPC decomposition $\eta_H\cdot\eta_O\cdot\eta_R$** | Renilson Eq. 5.4 | **HIGH** | Propulsion (Sec. 4.4) | Partially (uses lumped $\eta$) |
| 4 | **Propeller $K_T, K_Q, J$ canonical forms** | Newman Ch. 2 | **MEDIUM** | Propulsion (Sec. 4.4) | Constants only |
| 5 | **Mass Ratio + buoyancy-constrained sizing** | Rutherford Eqs. 7.1-7.6 | **MEDIUM** | Mass buildup (Sec. 4.6) | $\xi$-trim covers it |
| 6 | **Roughness allowance $\Delta C_F = +0.0004$** | Renilson Sec. 4.8.3.1 | **MEDIUM** | Hydro drag (Sec. 4.8) | $f_{\text{SLA}}$ factor used instead |
| 7 | **Control-surface $dC_L/d\delta$ effectiveness** | Hoerner 1985, Ch. IX | **MEDIUM** | Roll-authority gate | Not in model |
| 8 | **Stability derivative from tail geometry** | Hoerner 1985, Ch. XI | **MEDIUM** | NEW (stability gate) | Not in model |
| 9 | **Added-mass coeffs $k_x, k_y, k_z$ as $f(L/d)$** | Renilson Eqs. 3.63-3.64 | **LOW** | Added mass (Sec. 4.7) | Newman asymptotics cover it |
| 10 | **Water-exit rotor thrust $L_r = C_L\rho\omega_r^2 D_r^4$** | Li et al. Eq. 1 | **LOW** | Exit (only if self-powered) | Booster launch assumed |
| 11 | **Transverse-curvature $\Delta C_f$ correction** | Hoerner 1965, Eq. 32 | **LOW** | Hydro drag (Sec. 4.8) | Negligible at $l/d=10$ |

## Topics Where the Corpus Genuinely Adds Nothing

| Topic | Reason |
|---|---|
| **Wing structural weight (Topic 1)** | Hoburg wing-box is the only wing-weight model; no simpler UAV-wing monomial exists |
| **Material mass relations (Topic 6)** | No mass-per-unit-area or mass-fraction regressions for AUV hull skins |
| **Wetted-area formulas (Topic 7)** | No Myring-specific closed-form wetted area exists (requires numerical integration) |
| **Re-correction beyond power-law $C_f$ (Topic 8)** | No posynomial Re-dependent $C_D0$ correction beyond the standard $C_f$ power laws |
| **Water-exit thrust formula (Topic 9)** | Only the propeller thrust law exists; no analytic "exit thrust = f(vehicle params)" relation |
| **Fossen stability derivatives** | The Fossen PDF is a 30-page preview only; Ch. 6 (added mass matrix, hydrodynamic derivatives) is absent from the corpus |

## OCR Gaps That Block Further Extraction

1. **Renilson Chapter 3 manoeuvring coefficients** -- the empirical appendage-lift and
   hydrodynamic-derivative equations exist in the text but are on partially-OCR-failed pages.
   If stability constraints are added to the GP, re-OCR Renilson pp. ~80-120.
2. **Fossen Chapters 4 & 6** -- the full PDF is needed. The 30-page preview contains only
   front matter + TOC + Ch. 1.
3. **Hoerner Drag Chapter II ($C_f$ laws)** -- pages 8-10 failed in OCR. Not blocking
   (Renilson's ITTC line + power-law fit covers it).
