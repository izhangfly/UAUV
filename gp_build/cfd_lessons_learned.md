# UAUV OpenFOAM CFD — Complete Operations Manual

**Date:** 2026-08-02 · **First converged run:** Wing90 (deployed), α=0°, 50 m/s, C_D=0.0669, C_L=0.368
**Purpose:** Single-source reference for setting up, running, debugging, and validating every CFD
campaign. Read this BEFORE starting any new case. It covers every mistake we made so you don't
repeat them.

---

## 0. Pre-Flight: The First 5 Minutes of Any New Case

**Before you touch OpenFOAM, verify these five things. 90% of our errors were caught by one of them.**

### 0.1 The Five-Question Gate

| # | Question | Check | If wrong |
|---|---|---|---|
| 1 | Is this a free-air domain, not ground-effect? | `grep -c lowerWall system/blockMeshDict` must be 0 | Rewrite blockMeshDict §1 |
| 2 | Does flow direction match nose orientation? | Inlet face must be on the side the flow comes FROM; `0.orig/U` velocity must point INTO domain | Swap inlet/outlet OR negate velocity §1.3 |
| 3 | Does forceCoeffs dragDir match flow? | `grep dragDir system/forceCoeffs` must show same direction vector as flow velocity magnitude sign | C_D will be negative otherwise §3.3 |
| 4 | Are all snappyHexMesh patches in 0.orig boundary files? | `grep -c NBody 0.orig/U` must be ≥1 for all 5 patches | Fatal crash at decomposePar §2.1 |
| 5 | Is snappyHexMeshDict geometry block listing OUR STLs? | `grep motorBike system/snappyHexMeshDict` must return nothing | Re-mesh on motorcycle §4 |

**If all five pass, the case will run and produce physically-directional results.**
Fine-tuning may be needed, but you won't get zero forces, negative drag, or crashes.

### 0.2 The One-Minute MotorBike Audit

After copying the template, 30 seconds of grep finds every leftover:
```bash
cd ~/UAUV/cfd/my_new_case
echo "=== MOTORBIKE LEFTOVERS (all must return empty) ==="
grep -rn "motorBike\|motorBikeGroup\|motorBike.obj\|motorBike.eMesh" system/ --include="*" 2>/dev/null
grep -rn "lowerWall\|upperWall\|frontAndBack" 0.orig/ --include="*" 2>/dev/null
grep -rn "magUInf.*20\|lRef.*1\.42\|Aref.*0\.75\|1.42\|flowVelocity.*20" system/ 0.orig/ --include="*" 2>/dev/null
```

---

## 1. Domain Configuration

### 1.1 The motorBike ground-effect trap
The motorBike domain is a half-domain with a no-slip `lowerWall` at Z=0. If your vehicle is a
free-flying body, this wall creates ground-effect lift ~3× reality. **This was the hardest bug
to catch because the solver converged beautifully and gave "reasonable-looking" numbers.**

**Fix:** Our working free-air domain (X[-10, +7], Y[-6, +6], Z[-6, +6]) in `blockMeshDict`.
All far-field boundaries are `type patch` with slip conditions.

### 1.2 Domain sizing rules of thumb
| Direction | Minimum | Our value | Notes |
|---|---|---|---|
| Upstream | 5L | ~7 m (X=+7 face) | Flow comes from here |
| Downstream | 10L | ~9 m (X=-10 face) | Wake capture; we're 8.8L — extend to -12 for final validation |
| Lateral | 5L each | 6 m (Y±6) | Wing span is the limiting dimension, not body length |
| Vertical | 5L each | 6 m (Z±6) | | 

### 1.3 Flow direction: the single most error-prone setting
Vehicle nose is at X≈0, tail at X≈−1.02 (nose faces +X). Flow must hit the nose first:
- Inlet on +X face, velocity = (−50, 0, 0) — flow enters from +X, moves toward −X, hits nose
- `forceCoeffs dragDir = (−1, 0, 0)` — must be parallel to the freestream velocity vector
- `forceCoeffs liftDir = (0, 0, 1)` — perpendicular to dragDir and wing span (Y)

**Self-check:** after setup, verify `0.orig/U` inlet value AND `system/forceCoeffs` dragDir point
in the SAME Cartesian direction.

---

## 2. Boundary Conditions

### 2.1 Every snappyHexMesh patch MUST have BCs in ALL 5 field files
Our patches: NBody, VFin, HFin, Pivot, wing. Each needs entries in `0.orig/U`, `p`, `k`, `omega`, `nut`.
Missing = fatal at decomposePar. Template for wall BCs:

| Field | Wall type | Value |
|---|---|---|
| U | `noSlip` | — |
| p | `zeroGradient` | — |
| k | `kqRWallFunction` | `$internalField` or `uniform 1e-10` |
| omega | `omegaWallFunction` | `$internalField` or `uniform 1e-10` |
| nut | `nutkWallFunction` | `uniform 0` |

### 2.2 Include-file landmines
The motorBike `0.orig/include/frontBackUpperPatches` defines `upperWall` and `frontAndBack` — patches
that DON'T EXIST in a free-air domain. Remove any `#include "include/frontBackUpperPatches"` from
all 0.orig boundary files.

### 2.3 The `$variable` substitution pitfall
OpenFOAM uses `$variable` for dictionary expansion. When writing files from shell scripts:
- `<< 'EOF'` (quoted heredoc) → `$` is literal → `$turbulentKE` writes correctly
- `<< EOF` (unquoted) → `$` gets shell-expanded → use `\$` to escape → becomes `$` in output
- Single-quoted `echo '...'` → `\$` stays `\$` → BROKEN. **Always verify with `grep`.

### 2.4 Extra patch entries are warnings, not crashes
Patches in 0.orig that don't exist in the mesh produce "Cannot find patch...matching motorBikeGroup"
warnings. They don't crash but they clutter output and mask real issues. Clean them.

---

## 3. forceCoeffs — The Output That Matters

### 3.1 Quick-reference: our values vs motorBike defaults
| Setting | Our value | Wrong (motorBike) |
|---|---|---|
| `patches` | `(NBody VFin HFin Pivot wing)` | `(motorBikeGroup)` |
| `magUInf` | 50 | 20 |
| `lRef` | 1.021 | 1.42 |
| `Aref` | 0.075 | 0.75 |
| `rhoInf` (air) | 1.225 | 1 |
| `dragDir` | `(-1 0 0)` | `(1 0 0)` |
| `liftDir` | `(0 0 1)` | `(0 0 1)` |
| `CofR` | `(-0.51 -0.30 0)` | `(0.72 0 0)` |

### 3.2 dragDir sign IS the sign of your C_D
OpenFOAM computes `C_D = F · dragDir / (½ρU²A)`. If dragDir points opposite to the actual
aerodynamic drag force, C_D comes out negative. `grep dragDir system/forceCoeffs` before EVERY run.

### 3.3 Parsing the output file
Output at `postProcessing/forceCoeffs1/0/coefficient.dat`. Column map:
```
#Time  Cd(tot)  Cd(f)   Cd(r)   Cl(tot)  Cl(f)   Cl(r)   CmPitch  CmRoll  CmYaw  Cs  Cs(f)  Cs(r)
```
Skip headers: `grep -v "^#"`. Take mean of last 50 iterations for converged value:
```bash
tail -50 postProcessing/forceCoeffs1/0/coefficient.dat | grep -v "^#" | \
  awk '{s2+=$2; s5+=$5; n++} END{printf "C_D=%.6f C_L=%.6f\n", s2/n, s5/n}'
```

### 3.4 Convergence criterion: coefficient stability, not residuals
Converged ≠ residuals are low. Converged = **coefficients stopped changing**. Check:
```bash
# Mean of last 50 vs last 25 — difference should be <1%
tail -50 postProcessing/forceCoeffs1/0/coefficient.dat | grep -v "^#" | awk '{s+=$2;n++}END{printf "C_D(50): %.6f\n",s/n}'
tail -25 postProcessing/forceCoeffs1/0/coefficient.dat | grep -v "^#" | awk '{s+=$2;n++}END{printf "C_D(25): %.6f\n",s/n}'
```

---

## 4. snappyHexMesh — The Mesher's Quirks

### 4.1 Mandatory entries
- `castellatedMeshControls` MUST contain `refinementRegions {}` (even if empty). Missing = crash.
- `locationInMesh` must be in fluid, well clear of body, and stay valid through refinement.
  Our value: `(2 0 0)` — forward of the nose, off-axis.

### 4.2 Feature extraction chain
```
surfaceFeatureExtractDict references → STL files → produces .eMesh files
snappyHexMeshDict features block → references .eMesh files
```
The filenames must match at every link in the chain. If you rename `Wing90.stl` → `wing.stl`,
update BOTH dicts.

### 4.3 0 faces on thin features is normal
Our Pivot cylinder got 0 surface faces — too thin at this refinement level. The patch still exists
in the mesh (0 faces). This is harmless for the force budget (0 contribution). For detailed
wake/flow studies on thin features, increase local refinement.

---

## 5. Workflow & Automation

### 5.1 Single-case checklist (run this mentally before decomposePar)
```
[✓] blockMeshDict: free-air domain, no lowerWall/upperWall, correct vertex count
[✓] 0.orig/U: inlet velocity points INTO domain from inlet face
[✓] 0.orig/p,k,omega,nut: BC entries exist for NBody, VFin, HFin, Pivot, wing
[✓] 0.orig/include/initialConditions: flowVelocity correct magnitude and sign
[✓] 0.orig/*: no #include of frontBackUpperPatches or fixedInlet (we inline them)
[✓] forceCoeffs: patches list ours, dragDir matches flow, reference values UAUV
[✓] snappyHexMeshDict: geometry block has our STLs, refinementRegions {} present
[✓] surfaceFeatureExtractDict: references our STL filenames
[✓] controlDict: functions block has only forceCoeffs (stripped motorBike extras)
[✓] 0/ directory: freshly copied from 0.orig (not stale from previous run)
```

### 5.2 Rebuild from scratch (when in doubt)
```bash
rm -rf 0 processor* constant/polyMesh constant/extendedFeatureEdgeMesh postProcessing log.*
cp -r 0.orig 0
blockMesh && surfaceFeatureExtract && snappyHexMesh -overwrite && checkMesh
decomposePar -decomposeParDict system/decomposeParDict.6
mpirun -np 6 simpleFoam -parallel
reconstructPar
```

### 5.3 Re-run solver only (when only forceCoeffs or BCs changed, mesh unchanged)
```bash
rm -rf processor* postProcessing
decomposePar -decomposeParDict system/decomposeParDict.6
mpirun -np 6 simpleFoam -parallel
reconstructPar
```

---

## 6. Batching Multiple Cases

### 6.1 Architecture: one template, N cases
```
~/UAUV/cfd/
├── aero_template/          ← THE canonical template (never run directly)
├── aero_wing90/            ← deployed wing, α=0° (first case, verified)
├── aero_wing90_a4/         ← deployed wing, α=4° (angle sweep)
├── aero_wing60/            ← skew Λ=30°, α=0°
├── aero_wing60_a4/         ← skew Λ=30°, α=4°
└── ...
```
**Golden rule:** `aero_template/` is pristine. Every case copies from it, adapts one thing
(the wing STL + forceCoeffs settings), and runs. Never modify a case that might be needed
as a reference.

### 6.2 What changes between cases
| Change | Files to modify |
|---|---|
| Different wing angle | `constant/triSurface/wing.stl` (copy the correct WingXX.stl) |
| Different α | `0.orig/include/initialConditions` (flowVelocity), `system/forceCoeffs` (liftDir, dragDir) |
| Different speed (HYDRO) | `0.orig/include/initialConditions` (flowVelocity), `system/forceCoeffs` (magUInf, rhoInf) |

### 6.3 Batch runner skeleton
```bash
#!/bin/bash
# Batch α sweep for one wing mesh. Run inside openfoam shell.
CASE_DIR="$1"
cd "$CASE_DIR" || exit 1
for ALPHA in -4 -2 0 2 4 6 8 10 12; do
    Vx=$(python3 -c "import math; r=math.radians($ALPHA); print(50*math.cos(r))")
    Vz=$(python3 -c "import math; r=math.radians($ALPHA); print(-50*math.sin(r))")
    # Update flow
    echo "flowVelocity ($Vx 0 $Vz);" > 0.orig/include/initialConditions
    echo "pressure 0;" >> 0.orig/include/initialConditions
    echo "turbulentKE 0.24;" >> 0.orig/include/initialConditions
    echo "turbulentOmega 1.78;" >> 0.orig/include/initialConditions
    # Update force directions
    python3 -c "
import math; a=math.radians($ALPHA); sx=math.sin(a); cx=math.cos(a)
t=open('system/forceCoeffs').read()
t=t.replace('dragDir         ( -1 0 0 );', f'dragDir         ( {-cx:.6f} 0 {sx:.6f} );')
t=t.replace('liftDir         ( 0 0 1 );',   f'liftDir         ( {-sx:.6f} 0 {cx:.6f} );')
open('system/forceCoeffs','w').write(t)
"
    rm -rf 0 processor* postProcessing
    cp -r 0.orig 0
    decomposePar -decomposeParDict system/decomposeParDict.6 >/dev/null 2>&1
    mpirun -np 6 simpleFoam -parallel >/dev/null 2>&1
    reconstructPar >/dev/null 2>&1
    C_D=$(tail -50 postProcessing/forceCoeffs1/0/coefficient.dat | grep -v "^#" | \
          awk '{s+=$2;n++}END{printf "%.6f",s/n}')
    echo "$ALPHA,$C_D" >> results.csv
done
```

---

## 7. Validity Verification — Is This Result Real?

### 7.1 The four-gate validity check (run after every case)
```bash
# GATE 1: Signs are physically correct
C_D=$(tail -50 postProcessing/forceCoeffs1/0/coefficient.dat | grep -v "^#" | awk '{s+=$2;n++}END{printf "%.6f",s/n}')
# C_D must be positive; if negative, dragDir is flipped (§3.2)

# GATE 2: Coefficients are in the right ballpark
# Slender body at 50 m/s: C_D ~ 0.01-0.10 (too far outside = domain or BC problem)
# NACA 3612 at α=0°: C_L ~ 0.2-0.4 (much higher = ground effect or camber error)

# GATE 3: Coefficients have stabilized (not still drifting)
diff=$(python3 -c "print(abs($(tail -50 ... | awk ...) - $(tail -25 ... | awk ...)))")
# Difference between last 50 and last 25 iterations must be <1% of mean

# GATE 4: Residuals are in acceptable range
# U initial residuals ~10^-6, p ~10^-6, turbulence ~10^-8
```

### 7.2 Physical sanity checks by configuration
| Configuration | Expected C_D range | Expected C_L at α=0° |
|---|---|---|
| Deployed wing, clean | 0.03–0.10 | 0.2–0.4 (NACA 3612 camber) |
| Stowed wing (Λ=90°) | 0.01–0.03 (body only) | ~0 |
| Body only (no wing) | 0.01–0.02 | ~0 |
| HYDRO (same Re) | ~0.01 (higher Re → lower C_f) | similar trends |

### 7.3 When to distrust a run
- Any coefficient changes sign between iterations 400–500 (still transient)
- `μ_t/μ` pins at floor (~1) or ceiling (~10⁵) anywhere in the domain (turbulence model failure)
- Continuity error grows instead of shrinking
- Any single patch contributes >50% of total force (likely mesh/BC artifact)
- C_D changes >2% when doubling cell count (not grid-converged)

---

## 8. Self-Debugging Flowchart

```
Run fails with FATAL ERROR
    ↓
Error mentions "patchField entry" or "Cannot find patch"?
    → YES: A snappyHexMesh patch has no BC entry (§2.1). Add it to 0.orig/*.
    → NO: Continue.
    
Error mentions "motorBike.obj" or "motorBike.eMesh"?
    → YES: A dict still references motorBike geometry (§0.2). Update it.
    → NO: Continue.

Error mentions "refinementRegions"?
    → YES: Missing from snappyHexMeshDict (§4.1). Add `refinementRegions {}`.
    → NO: Continue.

Error mentions "locationInMesh" or 0 cells?
    → YES: Point is on body or outside domain (§4.1). Move it to (2, 0, 0).
    → NO: Continue.

Error mentions "negative volume"?
    → YES: blockMesh vertices wrong-handed. Reverse hex vertex order.
    → NO: Check logs for specific message.

Run completes but forces are all zero?
    → forceCoeffs patches list doesn't match mesh patches (§3.1). Fix.
    
Run completes but C_D is negative?
    → dragDir points opposite to flow (§3.2). Negate dragDir.
    
Run completes but C_L is far from expected range?
    → Possible ground effect (§1.1). Check domain for wall boundaries.
    → Possible wrong flow speed. Check initialConditions.
    
Run completes, values look right but change with mesh refinement?
    → Not grid-converged. Run at 2× and 4× cells, check Richardson extrapolation.
```

---

## 9. Reference: Our First Verified Run

| Parameter | Value |
|---|---|
| Wing | Wing90 (deployed, Λ=0°) |
| α | 0° |
| Speed | 50 m/s |
| **C_D** | **0.0669** |
| **C_L** | **0.368** |
| Cells | 11,319 |
| Domain | 17 × 12 × 12 m (free air) |
| Solver | simpleFoam, k-ω SST |
| Iterations | 500 |
| Residuals | Ux~10⁻⁶, p~10⁻⁶, k/ω~10⁻⁸ |

---

## 10. Template File Inventory — What Every File Does

| File | Role | MotorBike leftovers to check |
|---|---|---|
| `system/blockMeshDict` | Background mesh domain | `lowerWall`, `upperWall`, domain vertices |
| `system/snappyHexMeshDict` | Surface wrapping | `motorBike.obj`, `refinementBox`, feature files, patch names |
| `system/surfaceFeatureExtractDict` | Edge extraction | STL filenames |
| `system/forceCoeffs` | Force coefficient output | patches, reference values, dragDir |
| `system/controlDict` | Solver control + function objects | Included function object list |
| `system/fvSchemes` | Discretization schemes | Usually fine as-is |
| `system/fvSolution` | Solver tolerances + relaxation | Relaxation factors for speed |
| `system/decomposeParDict.6` | Parallel decomposition | Number of subdomains |
| `0.orig/U` | Velocity field + BCs | Inlet velocity, wall patch names, includes |
| `0.orig/p` | Pressure field + BCs | Outlet fixedValue, wall patch names |
| `0.orig/k` | Turbulent kinetic energy + BCs | Wall functions, `$turbulentKE` |
| `0.orig/omega` | Specific dissipation rate + BCs | Wall functions, `$turbulentOmega` |
| `0.orig/nut` | Turbulent viscosity + BCs | Wall functions |
| `0.orig/include/initialConditions` | Variable definitions | `flowVelocity`, `pressure`, turbulence values |
| `constant/transportProperties` | Fluid properties | ν (kinematic viscosity) |
| `constant/turbulenceProperties` | Turbulence model selection | RAS model type |
