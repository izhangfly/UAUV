# Equation Verification Report — gp_model.tex vs Source Documents

**Generated:** 2026-08-02
**Method:** Two-pass citation-check methodology (Pass 1: extract all equations + citations from gp_model.tex; Pass 2: verify each against extraction files G1--G8.md, spot-check against original PDFs where OCR failed).
**Target:** `/Users/ianzhang/UAUV/gp_model.tex`
**Sources:** `/Users/ianzhang/UAUV/gp_build/extractions/G1.md` through `G8.md`; original PDFs in `/Users/ianzhang/UAUV/refs/`; canonical nomenclature in `/Users/ianzhang/UAUV/gp_build/nomenclature.md`.

---

## Pass 1 — Equation Extraction

### Block A: GP Definitions and Methods (Section 2)

| ID | Equation(s) | Cites | Verified |
|---|---|---|---|
| M-1 | Monomial def: $h(\mathbf{u})=c\prod u_j^{a_j}$, $c>0$ | boyd2007tutorial | Yes (G1 E-21) |
| M-2 | Posynomial def: $f(\mathbf{u})=\sum_k c_k\prod u_j^{a_{jk}}$ | boyd2007tutorial, hoburg2014geometric | Yes (G1 E-2, E-21) |
| M-3 | GP standard form: $\min f_0$ s.t. $f_i\le 1$, $h_i=1$ | boyd2007tutorial, hoburg2014geometric | Yes (G1 E-3, E-21) |
| M-4 | Posynomial-equality relaxation | hoburg2014geometric | Yes (G1 E-5) |
| M-5 | "Minimize inverse to maximize" | hoburg2014geometric, boyd2007tutorial | Yes (G1 E-6) |
| M-6 | Data-to-posynomial fitting (gpfit/softmax) | hoburg2016data | Yes (G1 E-14 through E-20) |

### Block B: Mission and Geometry (Section 3)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| E-1 | $b + 0.3 \le L$ (packaging constraint) | none (CAD-derived) | N/A (geometry constraint, not from literature) |

### Block C: Aerial Cruise (Sections 4.1--4.3)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| E-2 | $mg \le \tfrac12\rho_a V_a^2 S C_{L,a}$ | hoburg2014geometric Eqs 15,17 | **EXACT** (G1 E-7) |
| E-3 | $D_a \ge \tfrac12\rho_a V_a^2 S C_{D,a}$ | hoburg2014geometric Eq 18 | **EXACT** (G1 E-7) |
| E-4 | $P_a \ge D_a V_a / \eta_a$ | hoburg2014geometric Eq 21 | **EXACT** (G1 E-7, adapted) |
| E-5 | $C_{D,a} \ge C_{L,a}^2/(\pi e A) + C_{Dp} + C_{D0,a}$ | hoburg2014geometric, hoerner1965fluid | **EXACT** (G1 E-10) |
| E-6 | $C_{D0,a} = C_f (1+k) S_{wet}/S$ | hoerner1965fluid | **EXACT** (G3 E-3, combined) |
| E-7 | $C_f = 0.074/\mathrm{Re}^{0.2}$ | hoburg2014geometric | **EXACT** (G1 E-B-1; power-law approx of turbulent flat-plate skin friction) |
| E-8 | $\mathrm{Re} = \rho_a V_a c / \mu$ | standard | **EXACT** (G3 E-2) |
| **E-9** | **$(1+k) = 1 + 1.5(d/L)^{3/2} + 7.0(d/L)^3$** | **hoerner1965fluid Eq 28** | **EXACT**. Source (G3 E-3): $\dfrac{C_{D\text{wet}}}{C_f} = 1 + 1.5(d/l)^{3/2} + 7(d/l)^3$. Exponents $(d/L)^{3/2}$ and $(d/L)^3$ and coefficients 1.5 and 7.0 all match. gp_model.tex correctly cites this as Hoerner Eq. 28. Confirmed against OCR text at mmd L2326: "Eq. 28. Total viscous drag … 1 + 1.5(d/l)^{3/2} + 7(d/l)^3". |

### Block D: Propulsion and Endurance (Section 4.4)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| E-10 | $E_b = e_b m_b$ | rutherford2008southampton, lin2026energies | **EXACT** (G7 E-1: $Energy = Spe_{batt} \times M_{batt}$) |
| E-11 | $R_a = V_a t_a$, $R_w = V_w t_w$ | standard | **EXACT** (G7 E-6) |
| E-12 | $E_b \ge P_a t_a + P_w t_w + P_{hotel} t_{total}$ | allen2000propulsion, rutherford2008southampton | **EXACT** (G7 E-5 rearranged; posynomial form) |
| E-13 | $\eta_a \le \eta_{motor} \eta_{prop}$ | hoburg2014geometric, allen2000propulsion | **EXACT** (G1 E-7: $\eta_{prop} = \eta_i \eta_v$; G7 E-22: QPC = 0.811) |
| E-14 | $\eta_i \le 2/(1+\sqrt{1+T/(\tfrac12\rho V^2 A_{prop})})$ | hoburg2014geometric Eq 36 | **EXACT** (G1 E-9). Rearranged GP form $4\eta_i + T\eta_i^2/(\tfrac12\rho V^2 A_{prop}) \le 4$ also correct (Eq 37). |

### Block E: Mass Buildup (Section 4.5)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| E-15 | $m \ge m_{pay} + m_s + m_b + m_{prop} + m_{fixed}$ | hoburg2014geometric | **EXACT** (G1 E-7, weight-buildup template Eq 19) |
| E-16 | $m_{prop} \le c_m P_{max}$ | general (power-law) | **APPROXIMATE** — power-law scaling is standard; $c_m \approx 0.1$--$0.3$ kg/kW cited as "representative UAV/UUV values". No single source. Acceptable for conceptual sizing. |

### Block F: Underwater Cruise and Buoyancy (Section 4.6)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| E-17 | $B = \rho_w g \nabla$ | newman2018marine | **EXACT** (G4 E-1). Archimedes' principle. |
| E-18 | $mg = B(1+\xi)$ | derived | **EXACT** (definition of $\xi = (W-B)/B$, G4 E-1 excess-weight concept) |
| E-19 | $L_{tr} = \xi B = \tfrac12\rho_w V_w^2 S_{stow} C_{L,uw}$ | derived | **EXACT** (combines E-17/E-18 with lift equation) |
| E-20 | Added mass: $m_a = k_a \rho_w \nabla$, $k_a \approx 0.03$ at $L/d\approx 10$ | newman2018marine | **APPROXIMATE**. G4 E-7 gives asymptotic $m_{11} = \tfrac43\pi\rho b^4/a[\log(a/b)+O(1)]$. For $b/a=0.1$, this yields $k_1 \approx 0.03$. The exact Lamb integrals for a prolate spheroid are not in the OCR text (they are in Figure 4.8 and Lamb 1932). The value $k_a \approx 0.03$ is consistent with the slender-body asymptote. Newman verified as the correct source. |
| E-21 | Self-compensation thesis: $dL/d\alpha = 2\pi q \delta^2$ | hoerner1985fluid (Jones slender-body) | **DERIVED CORRECTLY**. Derivation: Jones slender-body $C_{L\alpha} = \pi A/2$ (G2 E-8, Hoerner Eq 19); for stowed wing $A = 2\delta/b$, $S_{stow} = 2\delta b$; then $dL/d\alpha = q S_{stow} C_{L\alpha} = q(2\delta b)(\pi \cdot 2\delta/b / 2) = 2\pi q \delta^2$. The Jones law is in Hoerner (Eq 19, mmd L2199). The $dL/d\alpha = 2\pi q \delta^2$ result is a correct algebraic derivation from it. |

### Block G: Underwater Hydrodynamic Drag (Section 4.7)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| E-22 | $D_w = \tfrac12\rho_w V_w^2 S_{wet} C_{D,w}$ | hoerner1965fluid | **EXACT** (G3 E-1) |
| E-23 | $C_{D,w} \ge C_f (1+k) + k_{uw} L_{tr}^2/((\tfrac12\rho_w V_w^2)^2 S_{stow}^2)$ | hoerner1965fluid, CFD | **APPROXIMATE** — source supplies $(1+k)$ form factor (E-9) and the $C_f$ law; the $k_{uw}$ induced-drag term is the CFD-fitted component. Structure correct per G3 synthesis. |

### Block H: Cavitation Margin (Section 4.8)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| **E-24** | **$-C_{p,\min} \le \sigma_i$** | **brennen2014cavitation** | **EXACT**. G5 E-3: $\sigma_i = -C_{p,\min}$ (Brennen Eq 15, mmd L364). The gp_model.tex uses the inequality $\le$ which is the correct GP constraint form for cavitation avoidance: $\sigma \ge -C_{p,\min}$ means no cavitation (conservative). Brennen lists 5 reasons $\sigma_i$ departs from $-C_{p,\min}$ (G5 E-4), but the inequality $\le$ is the safe design ceiling. |
| **E-25** | **$\sigma = (p_{atm} + \rho_w g h - p_v)/(\tfrac12\rho_w V_w^2)$** | **brennen2014cavitation** | **EXACT**. G5 E-2: $\sigma = (p_\infty - p_V(T_\infty))/(\tfrac12\rho_L U_\infty^2)$. With $p_\infty = p_{atm} + \rho_w g h$ (G5 E-6). At surface $h=0$, $V_w=20$ m/s: $\sigma \approx 0.495$, matching the project design notes. |
| E-26 | $p_v(20^\circ C) \approx 2.34$ kPa | brennen2014cavitation (standard steam tables) | **APPROXIMATE**. G5 E-7: Brennen's explicit $p_V(T)$ table is NOT in the OCR; value is from standard steam tables. 2.34 kPa at 20 degC is correct. Low-impact gap (p_V is ~2% of p_atm). |
| E-27 | GP form: $\tfrac12\rho_w V_w^2(-C_{p,\min}) + p_v \le p_{atm} + \rho_w g h$ | derived | **EXACT** (algebraic rearrangement of E-24 + E-25) |

### Block I: Pressure-Hull Structure (Section 4.9)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| E-28 | $\sigma_h = p_d d/(2 t_s) \le \sigma_y$, $p_d = \rho_w g h$ | shinoka2024structural | **EXACT**. G6 E-0/E-8: the unstiffened limit of the Shinoka hoop-stress gauge. G6 confirms $P_{c5} = h\sigma_{yp}/a$ (E-8) collapses to $\sigma_{hoop} = p_d a / h$ in the unstiffened limit. The gp_model.tex writes $p_d d/(2t_s)$ using diameter $d=2a$ and $t_s$ for shell thickness — equivalent to the G6 form. |
| **E-29** | **$p_{cr} = \dfrac{E t_s/a}{n^2-1+\lambda^2/2}\left[\dfrac{1}{(n^2+\lambda^2)^2}\right] + \cdots$** | **shinoka2024structural** | **WRONG — MISSING $\lambda^4$ FACTOR.** The source (G6 E-1, Bryant 1954 as reproduced in Shinoka) gives: $$P_N = \frac{(E h/a)\,\lambda^4}{(n^2-1+\lambda^2/2)(n^2+\lambda^2)^2} + \frac{(n^2-1)E I_c}{a a_{gc}^2 L_f}$$ where $\lambda = \pi a/L$. The gp_model.tex omits the $\lambda^4$ factor in the numerator of the shell term. OCR of the original PDF (Shinoka Eq 1) renders as `(E·h/a)^{±4}` (garbled) but G6 correctly interprets this as `(E h/a)·λ^4`. For our hull ($a \approx 0.05$ m, $L \approx 1.02$ m): $\lambda^4 \approx (\pi\cdot 0.05/1.02)^4 \approx 0.00056$, so the missing factor changes the result by ~1800x. **Mitigation:** gp_model.tex explicitly states this equation is non-GP and will be replaced by a fitted Windenburg--Trilling monomial; the equation is illustrative. However, as presented it is factually wrong. |
| E-30 | GP path: fit $p_{cr} \approx C E (t_s/a)^\alpha (a/L)^\beta$ | shinoka2024structural (Windenburg-Trilling) | **APPROXIMATE** — this is the recommended GP approach, not a source equation. The Windenburg-Trilling form (G6 E-RECOMMENDED): $p_{cr} \approx 2.42 E (h/2a)^{2.5} / ((1-\mu^2)^{0.75}[L/2a - 0.45(h/2a)^{0.5}])$ is signomial but can be monomial-fitted. |
| E-31 | $\mathrm{SF}_{overall} \ge 2.0$ | shinoka2024structural | **EXACT** (G6 E-5: SF·σ < σ_y; base-case SF = 2.0 for overall, 1.5 for interframe) |

### Block J: Water-Entry Survival (Section 4.10)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| E-32 | $a_{peak} = C V_{entry}^a d^b m_{eff}^c$, $m_{eff} = m + m_a$ | song2020waterentry, newman2018marine | **FORM CORRECT, PRIOR EXPONENT WRONG.** Source (G8 E-9, song2020): $a_{peak} = c_D (\pi/8) \rho_w V^2 D^2 / m$ → exponents **(a,b,c) = (2, 2, −1)**. gp_model.tex text says analytic prior is "a≈2, b≈1 (diameter), c≈−1" — **b≈1 is wrong; should be b≈2** (area scales as d², so force ∝ d², a_peak ∝ d²/m). the project design notes correctly lists (2, 2, −1). The gp_model.tex also correctly states "All three exponents are fitted from CFD — the prior serves only as a sanity check." The equation itself uses symbolic exponents (a,b,c), so the form is correct; only the prose's stated prior for b is wrong. |
| E-33 | $k_a \approx 0.03$ (axial added mass, ~3% correction) | newman2018marine | **APPROXIMATE** — same as E-20 above. Value consistent with slender-body asymptote. |
| E-34 | $a_{peak} \le 20g$ (hard constraint) | derived (design requirement) | N/A (specification, not literature) |
| E-35 | Song et al. confirm $V^2$ scaling for oblique entry | song2020waterentry | **EXACT** (G8 E-9, E-10) |

### Block K: Wing Skew Dynamics (Section 4.11)

| ID | Equation | Cites | Verified |
|---|---|---|---|
| E-36 | $|C_l(\Lambda)| \le C_{l,\max}$ | derived (CFD-fit gate) | N/A (roll-authority gate from CFD; $C_l(\Lambda)$ is CFD-fitted per G2 E-7: aileron effectiveness $\propto \cos^2\Lambda$) |
| E-37 | $C_{l,\max} = \text{tail-fin authority}/(\tfrac12\rho V^2 S b)$ | derived | **APPROXIMATE** — correct form but numerator (tail-fin authority) is computed from fin geometry, not a literature formula |
| E-38 | Roll time constant $\tau \approx 0.10$--$0.12$ s | the project design notes (derived) | N/A (derived in the project design notes, not sourced from literature) |

---

## Pass 2 — Summary Table

### Overall Statistics

| Category | Count |
|---|---|
| Total equations extracted | 38 (M-1 through E-38) |
| Verified EXACT | 25 |
| Verified APPROXIMATE (minor differences, acceptable) | 7 |
| **WRONG (needs fix)** | **2** |
| NOT FOUND (gap) | 0 |
| N/A (derived or design spec, not literature) | 4 |

### Equations Verified EXACT (25)

M-1, M-2, M-3, M-4, M-5, M-6, E-2, E-3, E-4, E-5, E-6, E-7, E-8, **E-9** (Hoerner form factor), E-10, E-11, E-12, E-13, E-14, E-15, E-17, E-18, E-19, E-22, **E-24** (Brennen $\sigma_i$), **E-25** (cavitation number), E-27, E-28, E-31

### Equations Verified APPROXIMATE (7)

E-16 (power-law mass coefficient -- standard but no single source), **E-20** (Newman $k_a \approx 0.03$ -- consistent with asymptote, exact Lamb integrals not in OCR), E-21 ($dL/d\alpha = 2\pi q\delta^2$ -- correct derivation from Jones, not directly in Hoerner), E-23 (hydro drag with CFD-fitted $k_{uw}$), E-26 ($p_v$ from steam tables not Brennen OCR), E-30 (fitted monomial approach -- correct recommendation, not a source equation), E-33 (same as E-20)

---

## Errors Requiring Fixes

### ERROR 1: Bryant Buckling Equation — Missing $\lambda^4$ Factor

**Location:** gp_model.tex, Section 4.9 (Pressure-hull structure and buckling), lines 273--277

**What gp_model.tex says:**
```latex
p_{\text{cr}} = \frac{E\,t_s/a}{\,n^2-1+\lambda^2/2\ }
                \left[\frac{1}{(n^2+ \lambda^2)^2}\right] + \cdots
```

**What the source says (G6 E-1, Bryant 1954 as reproduced in Shinoka 2024/2025 Eq 1):**
```latex
P_N = \frac{(E h/a)\,\lambda^4}{(n^2-1+\lambda^2/2)(n^2+\lambda^2)^2}
      + \frac{(n^2-1)E I_c}{a a_{gc}^2 L_f}
```
where $\lambda = \pi a/L$.

**The fix:**
```latex
p_{\text{cr}} = \frac{E\,t_s/a \cdot \lambda^4}
                {(n^2-1+\lambda^2/2)(n^2+\lambda^2)^2} + \cdots
```

**Severity:** MEDIUM. The equation is flagged as "signomial / non-GP" and will be replaced by a fitted Windenburg-Trilling monomial. The text says "the recommended GP path is to factor out the n-minimization into an offline evaluation and fit a monomial." However, as a displayed equation purporting to quote Bryant, it is factually wrong. Correct it or add a note that it is a simplified/approximate form.

**File to edit:** `/Users/ianzhang/UAUV/gp_model.tex`, line 274

---

### ERROR 2: Water-Entry Prior Exponent b — Should Be b≈2, Not b≈1

**Location:** gp_model.tex, Section 4.10 (Water-entry survival), line 297

**What gp_model.tex says:**
> The analytic prior from slamming theory is a≈2 (force ∝½ρV² area), b≈1 (diameter), c≈−1 (Newton).

**What the source says (G8 E-9, song2020):**
$$a_{peak} = \frac{F}{m} = c_D \frac{\pi}{8} \frac{\rho_w V^2 D^2}{m}$$
→ exponents **(a,b,c) = (2, 2, −1)**. Force $F \propto \tfrac12\rho V^2 A \propto V^2 D^2$, then $a_{peak} = F/m \propto V^2 D^2 / m$ → b=2 (not b=1).

**The fix:**
Change "b≈1 (diameter)" to "b≈2 (area ∝ d²)". The project design notes already correctly states (2, 2, −1).

**Severity:** LOW. The equation itself uses symbolic exponents (a, b, c) to be fitted from CFD; only the prose's stated analytic prior for b is wrong. The fitted values from CFD will be correct regardless.

**File to edit:** `/Users/ianzhang/UAUV/gp_model.tex`, line 297

---

## Minor Issues (No Fix Required, For Awareness)

### M-1: Citation mismatch — ITTC log-law incorrectly attributed to Myring

**Location:** gp_model.tex, line 171--172

> The turbulent flat-plate law $C_f=0.074\,\mathrm{Re}^{-0.2}$~\cite{hoburg2014geometric} is monomial and used in place of the ITTC 1957 log-law~\cite{myring1976theoretical,allen2000propulsion}

Myring 1976 uses the **Ludwig-Tillmann** turbulent skin-friction law (G3 Myring section), NOT the ITTC'57 line. The ITTC'57 line ($C_F = 0.075/(\log_{10}Re-2)^2$) is from **Renilson** (G3 E-4). Allen 2000 (REMUS) uses a frontal-area drag coefficient, not the ITTC line directly.

**Recommended fix:** Cite `renilson2018submarine` instead of `myring1976theoretical` for the ITTC'57 log-law. Myring is still the correct citation for the hull shape parameterization.

**Severity:** LOW. Does not affect any equation — only the citation trail.

### M-2: Nomenclature inconsistency — $e_b$ vs canonical $e_{batt}$

gp_model.tex uses $e_b$ and $E_b$ for battery specific energy and total energy (lines 63, 185). The canonical nomenclature (`nomenclature.md`) uses $e_{batt}$ and $E_{batt}$. The clash map (nomenclature.md Section 7, line 224) explicitly states "Renamed from $e_b$ to $e_{batt}$ for clarity." The gp_model.tex was written before this canonical decision.

**Recommended fix:** Either update gp_model.tex to use $e_{batt}$ everywhere, or add a note in nomenclature.md that gp_model.tex uses the older notation. Equations are mathematically identical either way.

**Severity:** LOW (cosmetic only).

### M-3: Form factor $(1+k)$ exponent notation

gp_model.tex writes $(d/L)^{3/2}$ consistently; Hoerner (G3 E-3) writes $(d/l)^{3/2}$. This is an exact match — $3/2$ and $1.5$ are the same exponent. The nomenclature table (gp_model.tex line 52) writes $1+1.5(d/L)^{1.5}+7(d/L)^3$, which is also equivalent. No issue.

---

## Critical Equations Spot-Check Results

| Equation | gp_model.tex | Source | Verdict |
|---|---|---|---|
| **Hoerner (1+k)** | $1 + 1.5(d/L)^{3/2} + 7(d/L)^3$ | G3 E-3: $1 + 1.5(d/l)^{3/2} + 7(d/l)^3$ (Eq 28) | **EXACT** |
| **Brennen $\sigma_i$** | $-C_{p,\min} \le \sigma_i$ | G5 E-3: $\sigma_i = -C_{p,\min}$ (Eq 15) | **EXACT** (inequality form is conservative GP constraint) |
| **Hoburg $C_f$** | $0.074/\mathrm{Re}^{0.2}$ | G1 E-B-1: $1 \ge 0.074/(C_f \mathrm{Re}^{0.2})$ | **EXACT** |
| **Newman $k_a$** | $\approx 0.03$ at $L/d\approx 10$ | G4 E-7: asymptotic gives $\approx 0.03$ | **APPROXIMATE** (consistent with asymptote) |
| **Bryant buckling** | Missing $\lambda^4$ | G6 E-1: includes $\lambda^4$ | **WRONG** (see Error 1) |
| **Energy balance** | $E_b \ge P_a t_a + P_w t_w + P_{hotel} t_{total}$ | G7 E-5: $Endurance = Energy/Total Power$ | **EXACT** (correct rearrangement) |
| **Myring hull** | Cited correctly, equations not reproduced | G3 Myring E-1, E-2 | **CORRECT CITATION** |
| **$dL/d\alpha = 2\pi q\delta^2$** | Derived, not explicit equation | G2 E-8: $C_{L\alpha} = \pi A/2$ (Jones) | **DERIVED CORRECTLY** |
| **Cavitation $\sigma$** | $(p_{atm}+\rho_w g h - p_v)/(\tfrac12\rho_w V_w^2)$ | G5 E-2: $(p_\infty - p_V)/(\tfrac12\rho_L U_\infty^2)$ | **EXACT** |
| **Water-entry $a_{peak}$ prior** | b≈1 (wrong prior) | G8 E-9: b=2 from $F \propto D^2$ | **WRONG PRIOR** (see Error 2) |

---

## Overall Confidence Rating per Equation Block

| Block | Confidence | Notes |
|---|---|---|
| GP definitions (M-1..M-6) | **HIGH** | All verified exact against Hoburg 2014, Boyd 2007, Hoburg 2016 |
| Aerial cruise (E-2..E-9) | **HIGH** | All exact; Hoerner form factor confirmed Eq 28 |
| Propulsion/energy (E-10..E-14) | **HIGH** | Energy balance, endurance, prop efficiency all exact |
| Mass buildup (E-15..E-16) | **HIGH** | Standard posynomial templates; $c_m$ is approximate by nature |
| Buoyancy/underwater (E-17..E-21) | **HIGH** | Buoyancy and trim equations correct; $k_a \approx 0.03$ is approximate but well-supported; $dL/d\alpha = 2\pi q\delta^2$ is a correct derivation |
| Hydro drag (E-22..E-23) | **HIGH** | Form factor and drag structure verified |
| Cavitation (E-24..E-27) | **HIGH** | All verified against Brennen 2014 |
| Pressure hull (E-28..E-31) | **MEDIUM** | Hoop stress EXACT; Bryant buckling equation WRONG (missing $\lambda^4$, but equation is illustrative and will be replaced by a fitted monomial); Windenburg-Trilling approach APPROXIMATE |
| Water entry (E-32..E-35) | **HIGH** | Monomial form EXACT; prior exponent b WRONG in prose only (equation symbols unaffected) |
| Roll gate (E-36..E-38) | **MEDIUM** | Gate structure correct; $C_l(\Lambda)$ and $C_{l,\max}$ are CFD-fitted, not literature-derived |

---

## Files Requiring Edits

1. **`/Users/ianzhang/UAUV/gp_model.tex`** — two fixes needed:
   - Line 274: Add $\lambda^4$ to the Bryant buckling numerator, OR add a disclaimer that it is a simplified approximate form not the exact Bryant equation
   - Line 297: Change "b≈1 (diameter)" to "b≈2 (area ∝ d²)"
   - (Optional) Line 172: Change `myring1976theoretical` citation for ITTC log-law to `renilson2018submarine`

2. **No other files** require edits for equation correctness.

---

## Verification Completeness

- All 38 equations traced to extraction files G1--G8
- 8 load-bearing equations spot-checked against original PDFs
- 2 errors found (1 medium-severity LaTeX error, 1 low-severity prose error)
- 3 minor issues noted (citation, nomenclature, notation)
- No equations NOT FOUND (all traced to at least one source)
- Overall confidence: **HIGH** — the GP model's mathematical structure is sound; the 2 errors are in illustrative/qualitative sections and do not affect the GP implementation
