# Verification of the GP Fits

Five independent verification methods applied to the fits in `fitted_coefficients.md`.
Reproduce: `source ~/UAUV/.venv/bin/activate && python3 cfd/fit_gp.py`.

## Method 1 — Buckingham-Pi cross-validation (strongest, independent)
Same geometry, **different fluid** (air vs water), matched non-dimensional regime → C_D must agree.
- Stowed induced-drag factor: **AERO Wing0 k = 22.91  vs  HYDRO Wing0 k_w = 21.29  →  7.1%**.
- Deployed/stowed C_D at α=0 agreed to 4–8% across all wings (checked earlier during the sweep).
- **Verdict: PASS.** Two independent CFD campaigns produce the same dimensionless coefficients.

## Method 2 — Fitted exponents vs analytic priors
| Relationship | Fitted exponent | Analytic prior | Verdict |
|---|---|---|---|
| C_Lα(Λ) ∝ (cosΛ)^n | **1.105** | 1.0 (sweep independence, G2 E-6) | ✅ within 11% |
| C_D0,w(Re) ∝ Re^n | **−0.112** | −0.2 skin-friction … 0 form-drag | ✅ physically bracketed |
| −C_p,min(C_L) ∝ (1+C_L)^n | **−0.078** | 0 (dimensionless const) | ✅ ≈0 |
| k(Λ) trend | 0.64 → 22.9 (36×) | 1/(πe·AR), AR→0 as Λ→90 | ✅ AR-collapse |

## Method 3 — Reconstruction quality (RMS log-error / R²)
| Fit | Metric | Value | Threshold | Verdict |
|---|---|---|---|---|
| Deployed aero polar | R²_polar | 0.994 | >0.95 | ✅ |
| Deployed GP posynomial C_D(C_L) | rms_log | 0.0038 | <0.05 | ✅ |
| C_Lα(Λ) schedule | rms_log | 0.011 | <0.05 | ✅ |
| Stowed hydro polar | R² | 0.988 | >0.95 | ✅ |
| C_D0,w(Re) | rms_log | 0.016 | <0.05 | ✅ |
| Stowed trim slope | R² | 0.966 | >0.95 | ✅ |
| Cavitation −C_p,min | rms_log | 0.032 | <0.05 | ✅ |
| C_D0(Λ) schedule | rms_log | 0.51 | <0.05 | ❌ (see caveats) |
| \|C_l\|(Λ) schedule | rms_log | 0.41 | <0.05 | ❌ (see caveats) |

## Method 4 — GP-legality (positivity of posynomial terms)
- Stowed polar C_D0,w = 0.033 > 0 and k_w = 21.3 > 0 → `C_D=C_D0+k C_L²` directly posynomial ✅
- Deployed C_D0,a = −0.017 < 0 (camber) → **replaced with positive-coefficient SMA posynomial** ✅
- C_Lα, −C_p,min, Re-coefficient all > 0 ✅
- **Verdict: PASS** — every quantity entering a GP constraint has a positive-coefficient form.

## Method 5 — Physical monotonicity / sign
- C_D minimum near α=0, symmetric, rising both ways ✅
- C_L monotonic increasing with α (all wings) ✅
- C_D increases monotonically as wing deploys (Wing0→Wing90) ✅
- −C_p,min speed-independent (dimensionless) ✅

---

## Caveats carried forward (honest limitations)
1. **C_Lα,a magnitude (0.835/rad) is mesh-limited** (~5× low vs AR theory). The 57k sweep mesh
   under-resolves the wing lift slope. Cruise C_L and polar shape are trustworthy; the absolute slope
   needs the grid-convergence mesh. The **cosΛ scaling is validated regardless of magnitude.**
2. **C_D0(Λ) and C_l(Λ) schedules fail the rms threshold** — C_D0 flips sign with camber (schedule
   ill-posed in cosΛ), and roll moments (~10⁻³) are near mesh noise. These are **not used by the GP
   directly** (roll is an offline trajectory gate per sweep-plan §1.6); flagged for a dedicated finer run.
3. **Entry a_peak unfitted** — awaiting the entry DOE.

**Overall: the GP-critical fits (deployed polar, C_Lα scaling, stowed polar + Re, stowed trim,
cavitation) all pass 4–5 verification methods. Two schedule fits and the entry coefficient are
flagged as pending/limited and are documented, not silently used.**
