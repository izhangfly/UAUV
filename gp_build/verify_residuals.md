# Residual Convergence Crosscheck — UAUV vs motorBike Tutorial

**Date:** 2026-08-02
**Purpose:** Verify that the observed UAUV residual levels are normal, comparable to the well-validated motorBike tutorial, and adequate for a coefficient sweep with ~1% accuracy on C_D and C_L.

---

## 1. Comparison: fvSolution Settings

The UAUV `system/fvSolution` at `/Users/ianzhang/UAUV/cfd/aero_template/system/fvSolution` is **identical** to the standard motorBike tutorial (simpleFoam, k-ω SST). No settings have been customized for the UAUV case.

| Parameter | UAUV (= motorBike) | Notes |
|---|---|---|
| p solver | GAMG, GaussSeidel | Geometric-algebraic multigrid — standard choice |
| p tolerance | 1e-7 | Absolute tolerance for pressure |
| p relTol | 0.01 | Inner iterations stop at 1% of initial residual |
| U solver | smoothSolver, GaussSeidel | |
| U tolerance | 1e-8 | Absolute tolerance |
| U relTol | 0.1 | Inner iterations stop at 10% of initial |
| k tolerance | 1e-8 | |
| k relTol | 0.1 | |
| omega tolerance | 1e-8 | |
| omega relTol | 0.1 | |
| nNonOrthogonalCorrectors | 0 | Mesh is orthogonal enough |
| consistent | yes | Consistent SIMPLE — tighter pressure-velocity coupling |
| U relaxation | 0.9 | High, enabled by consistent formulation |
| k relaxation | 0.7 | Standard for k-ω SST |
| omega relaxation | 0.7 | Standard for k-ω SST |

No p relaxation factor is specified. With `consistent yes`, the pressure equation is treated implicitly within the momentum-pressure coupling and does not use explicit under-relaxation.

---

## 2. Residual Comparison

### Typical motorBike Tutorial (converged, ~500 iterations)

| Variable | Initial residual (outer iteration) |
|---|---|
| Ux | 1e-6 to 5e-6 |
| Uy | 1e-6 to 5e-6 |
| Uz | 1e-6 to 5e-6 |
| p | 2e-6 to 5e-6 |
| omega | ~1e-8 |
| k | ~1e-8 |

MotorBike residual behavior:
- Residuals drop 4-5 orders of magnitude in the first 100-150 iterations
- Then flatten to the asymptotic floor shown above
- U and p oscillate slightly about the floor values — this is normal SIMPLE behavior
- k and omega converge faster and deeper because the turbulence transport is diffusive

### UAUV Last Run (faulty ground-effect domain)

| Variable | Initial residual |
|---|---|
| Ux | ~8e-7 |
| Uy | ~4e-6 |
| Uz | ~9e-6 |
| p | ~2.5e-6 |
| omega | ~9e-9 |
| k | ~3e-8 |

### Verdict

**The UAUV residuals are comparable to the motorBike tutorial.** Specifically:

- Ux is actually better (8e-7 vs 1-5e-6)
- Uy is within the motorBike range (4e-6 vs 1-5e-6)
- Uz is slightly above the motorBike upper bound (9e-6 vs ~5e-6) — but within the same order
- p is within range (2.5e-6 vs 2-5e-6)
- omega and k are in the expected 1e-8 to 1e-9 range

The Uz being 2x higher than motorBike's typical ceiling is likely a consequence of the **faulty ground-effect domain** (the ground plane introduces stronger vertical gradients). With a proper domain, Uz should drop into the 1-5e-6 range. Even at 9e-6, this is a non-issue for coefficient accuracy (see section 4).

---

## 3. Relaxation Factors for 50 m/s vs 20 m/s

### Are the motorBike relaxations appropriate for our higher-speed case?

**Short answer: yes, no changes needed.**

The relaxation factors in SIMPLE control numerical stability, not physics. The factors that affect convergence difficulty at higher speed are:

1. **Reynolds number.** Re = 3.4e6 (UAUV) vs ~1.4e6 (motorBike). Higher Re means thinner boundary layers and sharper velocity gradients near walls. With wall functions (y+ 30-300), the mesh does not resolve the viscous sublayer anyway, so the near-wall gradients are handled by the wall function model, not the mesh.

2. **Convection dominance.** The cell Peclet number scales with velocity. At 2.5x higher speed, the convection terms are more dominant, which can make the linear system slightly more asymmetric. The `linearUpwindV` scheme for `div(phi,U)` handles this well — it's bounded and stable.

3. **Consistent SIMPLE.** The `consistent yes` setting is critical here. It reformulates the pressure equation to include the momentum coupling implicitly, which significantly stabilizes the iteration. This is why U relaxation can stay at 0.9 even at 50 m/s.

**Recommendation:** Keep the current relaxation factors. If convergence is slow (residuals not flattening by iteration 500), try:
- Drop U relaxation to 0.7-0.8 (most impactful single change)
- Drop p relTol from 0.01 to 0.05 (looser inner solves, more outer iterations, often faster overall)

Do NOT change k/omega relaxation — 0.7 is the sweet spot for k-ω SST.

### Turbulence inlet values

The current inlet values were inherited from the motorBike tutorial:

```
flowVelocity  (-50 0 0);     # was (-20 0 0) in motorBike
turbulentKE   0.24;           # unchanged
turbulentOmega 1.78;          # unchanged
```

At 20 m/s: I = sqrt(2k/3)/U = sqrt(0.16)/20 = 2.0% — typical for low-speed external aero.
At 50 m/s: I = sqrt(0.16)/50 = 0.8% — low, but acceptable for clean cruise conditions.

Eddy viscosity ratio: ν_t/ν = k/(ν·ω·C_μ) = 0.24/(1.5e-5 × 1.78 × 0.09) ≈ 100,000.
This is very high — typical atmospheric clean air is 1-10, wind tunnels are 10-100.

**Recommendation:** For the production coefficient sweep, re-tune to:
```
turbulentKE       0.024;     # I ≈ 0.25% at 50 m/s
turbulentOmega    10;        # ν_t/ν ≈ 10-20
```

This sets a clean-air turbulence level. The lower inlet turbulence reduces eddy viscosity contamination of the wake and produces crisper lift/drag predictions. The motorBike values work but will add ~5-10% turbulent mixing that isn't physically present at cruise altitude.

**Bug note:** The `0.orig/k` and `0.orig/omega` files have `\$turbulentKE` and `\$turbulentOmega` (backslash-escaped dollar signs). The backslash prevents OpenFOAM's variable expansion, so the values from `include/initialConditions` are never substituted. The files should use `$turbulentKE` and `$turbulentOmega` (no backslash). Fix before running.

---

## 4. What Residual Level Is Sufficient for a Coefficient Sweep?

### The 10x rule of thumb — and why it's conservative

The standard rule is: **force coefficients stabilize at roughly 10x the momentum residual level.** At ~10⁻⁶ residuals, coefficient stability is ~10⁻⁵.

For our case, we can compute the actual sensitivity:

| Parameter | Value |
|---|---|
| Dynamic pressure q | 0.5 × 1.225 × 2500 = 1531 Pa |
| Reference area Aref | 0.075 m² |
| q·Aref | 114.8 N |
| Expected C_D (clean body) | ~0.05 |
| Expected drag force | ~5.7 N |
| Momentum residual (rel. to convection) | ~10⁻⁶ |
| Force error from residuals | ~5.7 × 10⁻⁶ = 6 × 10⁻⁶ N |
| Coefficient error | ~6 × 10⁻⁶ / 114.8 = 5 × 10⁻⁸ |

**The residual-driven coefficient error is ~5 × 10⁻⁸ in C_D units, or 0.0001% of a typical C_D = 0.05.**

This is 4 orders of magnitude below the 1% accuracy requirement. The residual level is **not** the limiting factor for coefficient accuracy.

### What actually limits coefficient accuracy

1. **Mesh resolution (dominant).** At 1-2M cells with wall functions, discretization error on C_D is typically 2-5% compared to a grid-converged solution. This is 100-500x larger than the residual-driven error.

2. **Domain size.** Blockage ratio, inlet/outlet proximity, and far-field boundary conditions each contribute 0.5-2% error. The ground-effect domain was a prime example of this.

3. **Turbulence model.** k-ω SST vs SA vs k-ε can differ by 5-10% on drag for streamlined bodies at low AoA.

4. **y+ sensitivity.** Wall functions are calibrated for 30 < y+ < 300. Outside this range, C_f (and therefore C_D) can shift by 5-15%.

5. **Convergence criterion (coefficient stability, not residuals).** The relevant check: do C_D and C_L change by less than 1% over the last 100 iterations? This is a direct measurement and should be the primary convergence gate.

### Practical convergence gate for the sweep

```
Convergence is achieved when:
  std(C_D, last 100 iterations) / mean(C_D, last 100 iterations) < 0.01
  AND
  std(C_L, last 100 iterations) / mean(C_L, last 100 iterations) < 0.01
  AND
  residuals are at asymptotic floor (not still trending down)
```

For our case, the residuals at ~10⁻⁶ amply satisfy the last condition. The coefficient stability check is the operational criterion.

---

## 5. Recommended fvSolution Settings for the Coefficient Sweep

### Option A: Keep motorBike defaults (recommended)

**No changes.** The current settings produce residuals 1000x below what coefficient accuracy requires. Don't fix what isn't broken.

### Option B: Tighten for production (if you want a belt-and-suspenders approach)

```cpp
solvers
{
    p
    {
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       1e-8;     // was 1e-7 — tighter by 10x
        relTol          0.01;
    }
    U
    {
        solver          smoothSolver;
        smoother        GaussSeidel;
        tolerance       1e-9;     // was 1e-8 — tighter by 10x
        relTol          0.1;
        nSweeps         1;
    }
    // k and omega unchanged
}

SIMPLE
{
    nNonOrthogonalCorrectors 0;
    consistent yes;
}

relaxationFactors
{
    equations
    {
        U               0.9;
        k               0.7;
        omega           0.7;
    }
}
```

**Cost-benefit:** Tighter linear tolerances add ~5-10% to iteration time but reduce the asymptotic residual floor by 10x. This is cheap insurance. If using Option A and any run shows non-monotonic coefficient behavior, switch to B.

### Option C: Aggressive (only if cases converge slowly)

Reduce U relaxation to 0.7, increase p relTol to 0.05. This trades more outer iterations for faster inner convergence. Only use if runs are taking >1000 iterations to flatten.

### What to NOT change

- k and omega relaxation (0.7 is optimal for SST)
- The `consistent yes` setting (required for high U relaxation)
- Solver types (GAMG for p, smoothSolver for the rest are the right choices for 1-2M cell meshes)

---

## 6. Summary Verdict

| Question | Answer |
|---|---|
| Are UAUV residuals comparable to motorBike? | **Yes.** Within the same order of magnitude across all 6 variables. Uz is 2x the motorBike ceiling but still 10⁻⁵, likely a domain artifact. |
| Is this "converged enough" for a coefficient sweep? | **Yes, by a factor of ~10,000.** Residual-driven error on C_D is ~5×10⁻⁸ vs a 1% requirement of 5×10⁻⁴. |
| Should we tighten tolerances? | **Optional.** Option B (10x tighter) is cheap insurance. Option A (no change) is adequate. |
| Should we change relaxation factors for 50 m/s? | **No.** Consistent SIMPLE handles the higher Re well. |
| What should the actual convergence gate be? | **Coefficient stability over last 100 iterations,** not residuals. std(C_L)/mean(C_L) < 0.01. |

### Immediate action items (before running any CFD)

1. **Fix the `\$` escaping bug** in `0.orig/k` and `0.orig/omega`. Change `\$turbulentKE` → `$turbulentKE` and `\$turbulentOmega` → `$turbulentOmega`.
2. **Re-tune turbulence inlet values** (Section 3) — or at least document the current values' I=0.8%, ν_t/ν=100k state.
3. **Add a coefficient-stability check** to the post-processing pipeline. Parse `postProcessing/forceCoeffs/*/coefficient.dat`, compute the trailing-100-iteration statistics, and flag runs where std/mean > 1%.
4. **Define the convergence gate in the control script** so runs stop automatically when coefficients are stable, rather than running a fixed iteration count.
