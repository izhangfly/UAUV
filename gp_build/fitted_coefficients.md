# CFD-Fitted GP Coefficients

**Generated:** 2026-08-03 by `cfd/fit_gp.py` from `cfd/database/*.csv` (not hand-entered numbers).
**Machine-readable:** `gp_build/fits/fit_results.json` (includes raw data arrays for re-plotting).
**Plots:** `gp_build/fits/plots/*.png` (regenerate with `cfd/plot_fits.py`).
**Method:** gpfit (Hoburg 2016) — monomial = log-log least-squares (≡ gpfit max-affine K=1);
multi-term drag polar = softmax-affine (SMA). Convention: Λ = 90 − WingXX° (0 = deployed).

---

## 1. AERO — deployed wing (Λ=0°, Wing90, 50 m/s air)

| Quantity | Fitted value | GP constraint closed | Fit quality |
|---|---|---|---|
| Cruise operating point | C_L = 0.365, C_D = 0.0670 (α=0°) | lift `mg ≤ ½ρV²S·C_L`; power `P_a ≥ D_a V_a/η` | exact (measured) |
| Induced-drag factor | k_a = 0.638 | drag polar `C_D,a ≥ k C_L²/(...) + C_D0` | R²=0.994 |
| Lift-curve slope | **C_Lα,a = 0.835 /rad** ⚠ | lift/trim | R²=1.000 |
| GP-legal polar | `C_D(C_L)` = 2-term posynomial (SMA) | aerial profile drag | rms_log = 0.0038 |
| Zero-lift intercept | C_D0,a = −0.017 (camber offset) | — | see note |

> ⚠ **C_Lα,a = 0.835/rad is ~5× below the AR≈6.7 thin-airfoil expectation (~4.8/rad).** The 57k-cell
> sweep mesh under-resolves the wing's α-response. The **cruise C_L (0.365) and drag polar are trustworthy**
> (camber lift is captured, R²≈0.99); the absolute *slope* needs the grid-convergence mesh before the GP
> relies on off-design α behaviour. The **cosΛ scaling of C_Lα (below) is still validated** independent of magnitude.
>
> **Note on C_D0,a < 0:** the NACA-3612 camber puts the drag bucket at C_L≈0.2, so the un-shifted
> `C_D0+kC_L²` extrapolates negative at C_L=0 (GP-illegal). The GP instead uses the **positive-coefficient
> posynomial `C_D(C_L)`** (rms 0.0038) or the measured cruise operating point.

## 2. AERO — Λ-schedules (oblique-wing characterization)

| Fit | Equation | Prior | rms_log | Status |
|---|---|---|---|---|
| Lift slope vs skew | **C_Lα(Λ) = 0.847·(cosΛ)^1.105** | ∝ cosΛ (sweep independence) | 0.011 | ✅ validates prior |
| Induced factor vs skew | k(Λ): 0.638 (Λ=0) → 22.9 (Λ=90) | `1/(π e AR)`, AR→0 as stows | — | ✅ AR-collapse confirmed |
| Zero-lift drag vs skew | C_D0(Λ) = 0.0093·(cosΛ)^−1.0 | ~const+rise | 0.51 | ⚠ poor (camber sign flip) |
| Roll coefficient vs skew | \|C_l\|(Λ) = 0.0011·(cosΛ)^−0.17 | ∝ cos²Λ | 0.41 | ⚠ near noise floor |

> The **C_Lα ∝ cosΛ result (exponent 1.105 vs prior 1.0, rms 0.011) is a clean confirmation of the
> sweep-independence principle** for this oblique wing. The k(Λ) collapse (0.64→22.9, a 36× rise) is the
> aspect-ratio collapse as the wing folds. C_D0(Λ) and C_l(Λ) schedules are unreliable (camber sign change;
> roll moments ~10⁻³ are near mesh noise) — **flagged for a finer dedicated run if the trajectory sim needs them.**

## 3. HYDRO — stowed wing (Λ=90°, Wing0, water)

| Quantity | Fitted value | GP constraint closed | Fit quality |
|---|---|---|---|
| Zero-lift drag | C_D0,w = 0.0332 | underwater drag polar `D_w = ½ρ_w V² S_wet C_D,w` | R²=0.988 |
| Induced-drag factor | k_w = 21.29 | (same) | R²=0.988 |
| Re-dependence | **C_D0,w(Re) = 0.185·Re^−0.112** | Re-scaling of polar | rms_log=0.016 |
| Stowed trim slope | **dC_L,uw/dα = 0.053 /rad** | ξ-trim balance `L_tr = ½ρ_w V² S_stow C_L,uw` | R²=0.966 (n=20) |

> The Re exponent −0.112 sits between pure skin-friction (−0.2) and form-drag (0), consistent with a
> mixed friction/pressure-drag body. The tiny stowed lift slope (0.053/rad) is physically correct — the
> folded wing is a near-flat body of revolution.

## 4. CAVITATION — suction peak (Wing0 & Wing90, V_w 5–20, h 0–10 m)

| Quantity | Fitted value | GP constraint closed | Fit quality |
|---|---|---|---|
| Suction peak | −C_p,min ∈ [1.02, 1.16], **max 1.16** (conservative gate) | cavitation `σ ≥ −C_p,min` | — |
| GP form | **−C_p,min = 1.132·(1+C_L)^−0.078** | (same) | rms_log=0.032 |

> −C_p,min is nearly constant (dimensionless, exponent ≈0 as it must be). **Design consequence:** with
> −C_p,min≈1.13, surface cavitation (h=0) onsets at V_w ≈ 13 m/s (σ = −C_p,min), so the 20 m/s sprint
> cavitates at the surface but is cavitation-free below ~4 m depth (σ rises with hydrostatic head).

## 5. ENTRY — a_peak = C·V^a·d^b·m^c  →  **PENDING**

Entry DOE not yet run (1 validation case only). Fit deferred until `batch_entry_fixed.sh` completes.
Analytic prior (song2020): exponents (a,b,c) = (2, 2, −1); C encodes nose shape / entry angle via V_n = V·sin|θ|.

---

## Buckingham-Pi cross-check (independent verification)
Same geometry, air vs water, at matched Re → C_D must agree. **Stowed induced factor:
AERO Wing0 k = 22.9 vs HYDRO Wing0 k_w = 21.3 → 7.1% agreement.** Confirms both campaigns independently.
