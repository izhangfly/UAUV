# HYDRO CFD Batch Audit

**Date:** 2026-08-03
**Scope:** Full diagnostic trace of the inlet boundary condition bug affecting both AERO and HYDRO campaigns.
**Status:** ALL results from both campaigns are invalid for alpha sweeps. The root cause is a single stale file propagation issue.

---

## 1. Root Cause

**The `0.orig/U` files in all existing case directories have hardcoded `uniform (-50 0 0)` at the inlet and outlet boundaries, instead of `value $internalField;`.**

This means the inlet boundary condition is locked at 50 m/s in the pure -X direction, regardless of what `include/initialConditions` specifies for `flowVelocity`. The internal field is initialized correctly via the `$flowVelocity` macro, but in steady-state simpleFoam, the inlet BC dominates and the flow converges to a uniform 50 m/s in -X across the entire domain.

### Evidence chain

| File | Inlet value | Status |
|---|---|---|
| `/Users/ianzhang/UAUV/cfd/aero_template/0.orig/U` | `value $internalField;` | CORRECT (template was fixed) |
| `/Users/ianzhang/UAUV/cfd/hydro_template/0.orig/U` | `value $internalField;` | CORRECT (template was fixed) |
| `/Users/ianzhang/UAUV/cfd/cases/aero/Wing0/0.orig/U` | `value uniform (-50 0 0);` | **BUG** |
| `/Users/ianzhang/UAUV/cfd/cases/aero/Wing10/0.orig/U` | `value uniform (-50 0 0);` | **BUG** |
| ... all 10 AERO cases ... | `value uniform (-50 0 0);` | **BUG** |
| `/Users/ianzhang/UAUV/cfd/cases/hydro/Wing0/0.orig/U` | `value uniform (-50 0 0);` | **BUG** |
| `/Users/ianzhang/UAUV/cfd/cases/hydro/Wing10/0.orig/U` | `value uniform (-50 0 0);` | **BUG** |
| `/Users/ianzhang/UAUV/cfd/cases/hydro/Wing20/0.orig/U` | `value uniform (-50 0 0);` | **BUG** |
| HYDRO Wing30-Wing90 | Cases not yet created | N/A |

### How it happened

1. The AERO and HYDRO templates originally had hardcoded `uniform (-50 0 0)` in their `0.orig/U` files.
2. All 10 AERO cases were created (via `cp -r "$TEMPLATE" "$CASE"`) and meshed with this buggy U file.
3. The first 3 HYDRO cases (Wing0/10/20) were created by copying the buggy AERO `0.orig/` directory, then the HYDRO template's U was meant to overwrite it. But at that time, the HYDRO template also had the same hardcoded bug.
4. Later, both templates were fixed to use `$internalField` correctly.
5. On subsequent batch runs, the "reuse existing case" check (`if [ ! -f "$CASE/system/forceCoeffs" ]`) skips the setup block. Lines 40-43 of `batch_hydro.sh` only overwrite `transportProperties` and `forceCoeffs` — **not `0.orig/U`**.
6. Result: the stale buggy U files persist in all existing cases.

The hydro batch script line 35 does attempt to overwrite U:
```bash
cp "$TEMPLATE/0.orig/U" "$CASE/0.orig/"
```
But this line is inside the `if [ ! -f "$CASE/system/forceCoeffs" ]` block (lines 25-38), which is skipped when cases already exist.

---

## 2. Impact on HYDRO Results

### 2.1 The C_D = 2.66 mystery — solved

The solver pumps 50 m/s flow through the domain, but `forceCoeffs` uses `magUInf = 5` (correctly set by the batch Python regex). The coefficient computation is:

```
C_D = F_drag / (0.5 * rho * magUInf^2 * Aref)
```

With actual flow at 50 m/s but magUInf = 5, the denominator is (50/5)^2 = 100x too small, so C_D is inflated by ~100x.

| Quantity | Expected (water, 5 m/s) | Actual (water, 50 m/s inlet) |
|---|---|---|
| Flow velocity | 5 m/s | ~50 m/s |
| Dynamic pressure q | 12,500 Pa | 1,250,000 Pa |
| Estimated drag force | ~15 N | ~2,500 N |
| C_D (Aref=0.075) | ~0.016 | **~2.66** |
| Inflated by | — | **~166x** |

The factor of ~166x (not exactly 100x) is because C_D itself depends on Re, and Re differs by 10x between 5 m/s and 50 m/s in water.

### 2.2 The C_L "alpha sweep" is a trigonometric artifact

HYDRO Wing0 C_L varies from -0.238 (alpha=-4°) to +0.593 (alpha=+14°), which superficially looks like a lift curve. It is not. The actual flow is always at 0° alpha (pure -X from the inlet). The apparent C_L variation is the drag force projected through the alpha-rotated `liftDir`:

```
C_L(alpha) ≈ tan(alpha) * C_D(alpha=0)
```

Verification at alpha=14°: tan(14°) * 2.66 ≈ 0.249 * 2.66 ≈ 0.663. Observed C_L = 0.593. The difference is from the small true lift on the stowed wing and solver noise. At alpha=-4°: tan(-4°) * 2.66 ≈ -0.186. Observed C_L = -0.238. Consistent.

### 2.3 What HYDRO actually measured

The HYDRO campaign measured exactly one thing: **C_D at effective alpha=0° with 50 m/s flow in water**. Every "alpha" in the CSV is a lie — the flow angle never changed. The three wings (Wing0, Wing10, Wing20) differ only because their geometries differ, giving different C_D values when meshed at different skew angles.

All 30 hydro runs (3 wings x 10 alphas) produced the same information as 3 runs at alpha=0° would have.

### 2.4 Other settings: verified correct

| Setting | Expected | Actual | Status |
|---|---|---|---|
| `transportProperties/nu` | 1.0e-06 (water) | 1.0e-06 | CORRECT |
| `forceCoeffs/rhoInf` | 1000 (water) | 1000 | CORRECT |
| `forceCoeffs/magUInf` | 5 (V_w) | 5 | CORRECT (set by regex) |
| `forceCoeffs/lRef` | 1.021 | 1.021 | CORRECT |
| `forceCoeffs/Aref` | 0.075 | 0.075 | CORRECT |
| `forceCoeffs/CofR` | (-0.51 -0.30 0) | (-0.51 -0.30 0) | CORRECT |
| `forceCoeffs/dragDir` | per-alpha trig | per-alpha trig | CORRECT (set by regex) |
| `forceCoeffs/liftDir` | per-alpha trig | per-alpha trig | CORRECT (set by regex) |
| `include/initialConditions` flowVelocity | per-alpha, per-V_w | per-alpha, per-V_w | CORRECT |
| `0.orig/U` inlet BC | `$internalField` | `uniform (-50 0 0)` | **BUG** |
| `0.orig/U` outlet BC | `$internalField` | `uniform (-50 0 0)` | **BUG** |

---

## 3. Impact on AERO Results

The same bug affects ALL 10 AERO cases. The AERO `0.orig/U` files all have `uniform (-50 0 0)` hardcoded.

### 3.1 AERO alpha sweep is also invalid

In the recovered AERO results (`aero_results_recovered.csv`), C_D and C_L are constant across all alphas for each wing:

**AERO Wing0 (stowed):**
| alpha | C_D | C_L |
|---|---|---|
| -4 to +14 | 0.03368-0.03391 | 0.00767 |

**AERO Wing90 (deployed):**
| alpha | C_D | C_L |
|---|---|---|
| -4 to +14 | 0.15339-0.15407 | -0.3382 |

The C_D variation within each wing is at the 5th significant digit — pure solver noise and dragDir projection artifacts. No aerodynamic alpha effect is present.

### 3.2 What AERO actually measured

The AERO campaign measured **C_D and C_L at alpha=0° for each of the 10 wing skew angles**. This is still useful — it gives the drag polar anchor point for each wing configuration. But:
- **C_L_alpha (lift slope) is unknown for all wings**
- **C_D0 and k (drag polar coefficients) are unknown**
- **C_l (roll moment during skew) is unknown**
- **C_m (pitching moment) vs alpha is unknown**

### 3.3 Why the AERO bug was harder to spot

For the AERO case, the hardcoded `uniform (-50 0 0)` happens to be exactly correct for alpha=0° and V=50 m/s. The bug only affects non-zero alpha runs, where the inlet should be angled. The velocity magnitude is correct (50 m/s), only the direction is wrong. This made the results look "reasonable" at first glance — C_D=0.034 for a streamlined body is plausible. The alpha sweep looked broken only when examining the CSV carefully and noticing zero variation.

---

## 4. Turbulence Initialization — Secondary Issue

Both AERO and HYDRO use the same turbulence initialization (`turbulentKE 0.24`, `turbulentOmega 1.78`), hardcoded in the batch scripts. These values correspond to:

| | Air, 50 m/s | Water, 5 m/s |
|---|---|---|
| Turbulence intensity I | ~0.8% | ~8% |
| Turbulent length scale | ~0.15 m | ~0.15 m |

For water at 5 m/s, 8% turbulence intensity is very high (typical freestream is <1%). This is not the cause of the C_D=2.66 anomaly, but it may affect boundary layer transition prediction and should be corrected when the campaigns are re-run. Appropriate values for water at 5 m/s, L=1.021 m, I=1%: k ≈ 0.00375, ω ≈ 0.12.

---

## 5. Batch Script Logic — Additional Observations

### 5.1 dragDir sign convention mismatch between AERO and HYDRO

**AERO batch (line 41):**
```bash
DX=$(python3 -c "import math;r=math.radians($ALPHA);print(math.cos(r))")
```
dragDir = (cos(alpha), 0, sin(alpha)) — positive x-component

**HYDRO batch (line 50):**
```bash
DX=$(python3 -c "import math;r=math.radians($ALPHA);print(-math.cos(r))")
```
dragDir = (-cos(alpha), 0, sin(alpha)) — negative x-component

The HYDRO version is physically correct for a vehicle with nose pointing in -X: the drag force on a stationary body in a -X flow should be in the -X direction, so `dragDir = (-1, 0, 0)` at alpha=0. The AERO version has the opposite sign. Both produce positive C_D values because OpenFOAM's convention makes it work out, but one of them has the wrong physical interpretation. This should be unified when the campaigns are re-run.

### 5.2 forceCoeffs template has stale magUInf = 50

The HYDRO template `forceCoeffs` has `magUInf 50` (line 30), inherited from the AERO template. The batch Python regex overwrites this to the correct V_w value at runtime, so it does not affect results. But the template default should be corrected to avoid confusion.

### 5.3 forceCoeffs comment says "air density" with rhoInf=1000

Cosmetic only. The HYDRO template `forceCoeffs` line 24 has:
```
rhoInf          1000;        // air density [kg/m3]
```
The value is correct for water; the comment is stale from the AERO template.

---

## 6. What Needs to Be Re-run

### Summary of valid vs invalid data

| Campaign | Runs done | Valid data | What was actually measured |
|---|---|---|---|
| AERO | 10 wings x 10 alphas = 100 | Only alpha=0° for each wing (C_D and C_L at one point) | Drag at 0° alpha, all 10 skew angles |
| HYDRO Phase 1 | 3 wings x 10 alphas = 30 | **NONE** (wrong velocity magnitude) | Garbage (50 m/s flow, coefficients scaled with 5 m/s ref) |
| HYDRO Phase 2 | Not run | — | — |
| HYDRO Phase 3 | Not run | — | — |

### Re-run requirements

1. Fix `0.orig/U` in ALL case directories to use `value $internalField;` at inlet and outlet (matching the current templates).
2. Fix turbulence initial conditions for water cases (k ≈ 0.004, ω ≈ 0.12 for I=1%).
3. Re-run the full AERO alpha sweep (100 runs).
4. Re-run the full HYDRO campaign (all 3 phases).
5. Unify dragDir sign convention between AERO and HYDRO batch scripts.

---

## 7. Verification Test

Before re-running everything, verify the fix on ONE case:

```bash
# In a hydro Wing0 case directory:
cd /Users/ianzhang/UAUV/cfd/cases/hydro/Wing0
# Fix the U file
cp /Users/ianzhang/UAUV/cfd/hydro_template/0.orig/U 0.orig/U
# Set alpha=0, V_w=5
echo "flowVelocity (-5 0 0);" > 0.orig/include/initialConditions
echo "pressure 0;" >> 0.orig/include/initialConditions
echo "turbulentKE 0.004;" >> 0.orig/include/initialConditions
echo "turbulentOmega 0.12;" >> 0.orig/include/initialConditions
# Set forceCoeffs
python3 -c "
import re;t=open('system/forceCoeffs').read()
t=re.sub(r'dragDir\s+\([^)]+\)','dragDir         ( -1 0 0 );',t)
t=re.sub(r'liftDir\s+\([^)]+\)','liftDir         ( 0 0 1 );',t)
t=re.sub(r'magUInf\s+\d+','magUInf         5',t)
open('system/forceCoeffs','w').write(t)
"
rm -rf 0 processor* postProcessing; cp -r 0.orig 0
decomposePar -decomposeParDict system/decomposeParDict.6
mpirun -np 6 simpleFoam -parallel
reconstructPar
# Expected C_D ≈ 0.01-0.02 (not 2.66)
tail -1 postProcessing/forceCoeffs1/0/coefficient.dat
```

If C_D comes out ~0.015 at alpha=0 with V_w=5 in water, the fix is confirmed.
