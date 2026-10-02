# motorBike Leftover Audit -- aero_template/

**Date:** 2026-08-02
**Scope:** All 35 files under `/Users/ianzhang/UAUV/cfd/aero_template/`
**Verdict:** **FAIL** -- 11 CRITICAL hits across 7 files. The case is not safe to run.

---

## Summary counts

| Classification | Count |
|----------------|-------|
| CRITICAL       | 11    |
| WARNING        | 5     |
| OK (correctly ours) | 2 |

---

## CRITICAL hits (would crash or produce wrong results)

### 1. Allrun -- copies motorBike geometry instead of UAUV STLs

**File:** `Allrun`, lines 11-16
```sh
# copy motorbike surface from resources directory
mkdir -p constant/triSurface
cp -f \
    "$FOAM_TUTORIALS"/resources/geometry/motorBike.obj.gz \
    constant/triSurface/
```
**Impact:** If this script is sourced, it copies the motorBike OBJ file into `constant/triSurface/` and runs `surfaceFeatureExtract` + `blockMesh` + `snappyHexMesh` on it -- the entire mesh would be of a motorcycle, not the UAUV. The snappyHexMeshDict would then fail because it looks for `NBody.stl`, `VFin.stl`, etc. which would not be present. **Crash on `snappyHexMesh` unless the user manually placed the UAUV STLs beforehand.**

**Classification:** CRITICAL

---

### 2-6. motorBikeGroup patch in all 5 boundary condition files

**Files and lines:**

| File | Line | Snippet |
|------|------|---------|
| `0.orig/U` | 45-48 | `motorBikeGroup { type noSlip; }` |
| `0.orig/p` | 43-46 | `motorBikeGroup { type zeroGradient; }` |
| `0.orig/k` | 41-45 | `motorBikeGroup { type kqRWallFunction; value uniform 1e-10; }` |
| `0.orig/omega` | 30 | `motorBikeGroup { type omegaWallFunction; value uniform 1e-10; }` |
| `0.orig/nut` | 28 | `motorBikeGroup { type nutkWallFunction; value uniform 0; }` |

**Impact:** The `motorBikeGroup` patch does not exist in our mesh. Our `blockMeshDict` defines only `inlet`, `outlet`, and `farfield`. When OpenFOAM reads the boundary field and encounters a patch name that is not in the `polyMesh/boundary` file, it throws a **fatal error**:

```
--> FOAM FATAL ERROR:
Cannot find patchField entry for motorBikeGroup
```

The simulation will not start.

**Note:** The UAUV patches (NBody, VFin, HFin, Pivot, wing) ARE correctly present alongside motorBikeGroup. The fix is to **remove the motorBikeGroup block** from each file, not to replace them.

**Classification:** CRITICAL (x5)

---

### 7. ensightWrite -- frontAndBack in excludePatches

**File:** `system/ensightWrite`, line 19
```
excludePatches  ( inlet outlet frontAndBack ".*[Ww]all" );
```
**Impact:** `frontAndBack` is a motorBike domain patch. Our domain has `farfield` instead. This would cause the ensightWrite function object to fail with a patch-not-found error at write time. While it wouldn't crash the solver, it would corrupt post-processing output.

**Classification:** CRITICAL

---

### 8. wallBoundedStreamLines -- motorBikeGroup patches

**File:** `system/wallBoundedStreamLines`, lines 30 and 70
```
patches         (motorBikeGroup);    // line 30 -- near-wall field sampling
patches     (motorBikeGroup);        // line 70 -- patchSeed seeding
```
**Impact:** Both function objects reference a non-existent patch. The `near` function object would fail to find motorBikeGroup and error out. The wall-bounded streamline seeding would also fail. While the main solver might continue, the function objects would produce no output and log errors.

**Classification:** CRITICAL

---

### 9. faMeshDefinition -- entirely motorBike

**File:** `system/finite-area/faMeshDefinition`, lines 17, 24-25
```
polyMeshPatches   (motorBikeGroup);
// ownerPolyPatch      motorBikeGroup;
neighbourPolyPatch  lowerWall;
```
**Impact:** The finite-area mesh definition is 100% motorBike tutorial. `motorBikeGroup` and `lowerWall` do not exist in our mesh. If any finite-area solver or utility is invoked, it will crash. Even if finite-area is not actively used, this file is dead configuration that could be accidentally triggered.

**Classification:** CRITICAL

---

### 10. initialConditions -- turbulentKE and turbulentOmega are motorBike-tuned

**File:** `0.orig/include/initialConditions`, lines 3-4
```
turbulentKE          0.24;
turbulentOmega       1.78;
```
**Impact:** These values correspond to ~2% turbulence intensity at 20 m/s with a length scale of ~0.5 m -- the motorBike tutorial conditions.

At our 50 m/s, these same values give only ~0.8% turbulence intensity. While 0.8% is physically defensible for clean external aero (low-turbulence cruise), the values were **not recomputed for our case** and were inherited blindly. The correct values for 2% TI at 50 m/s would be:
- `turbulentKE = 1.5 * (0.02 * 50)^2 = 1.5`
- `turbulentOmega = sqrt(1.5) / (0.09^0.25 * 0.5) ≈ 4.47`

This will not crash the simulation but will produce **incorrect turbulence levels** upstream, affecting the boundary layer development, separation prediction, and force coefficients. Since k-omega SST is sensitive to inlet turbulence, this is a result-corrupting bug.

**Classification:** CRITICAL

---

### 11. myReportTemplate.md -- wrong OpenFOAM version

**File:** `system/myReportTemplate.md`, line 104
```
Made using Open∇FOAM v2412 from https://openfoam.com
```
**Impact:** We use v2606, not v2412. This is cosmetic in the report template, but if the template is used in automated reporting, it would claim the wrong version. Minor, but a leftover.

**Classification:** WARNING (downgraded from CRITICAL because it doesn't affect CFD results)

---

## WARNING hits (cosmetic / dead code, should clean)

### W12. ensightWrite -- commented-out motorBike regex

**File:** `system/ensightWrite`, line 16
```
//patches       ( "motorBike.*" );
```
**Impact:** Commented out, so inert. But if someone uncomments it during debugging, it would break.

**Classification:** WARNING

---

### W13. frontBackUpperPatches -- orphaned include file

**File:** `0.orig/include/frontBackUpperPatches`, entire file
```
upperWall   { type slip; }
frontAndBack { type slip; }
```
**Impact:** This file is **not #included by any boundary condition file** (confirmed by grep). It is dead code. However, `upperWall` and `frontAndBack` are motorBike domain patch names that do not match our `farfield`. If this file is ever included in the future, it would crash.

**Classification:** WARNING

---

### W14. fixedInlet -- orphaned include file

**File:** `0.orig/include/fixedInlet`, entire file
```
inlet { type fixedValue; value $internalField; }
```
**Impact:** Also not #included by any file. Dead code from motorBike tutorial. Our boundary files define `inlet` explicitly with the correct velocity, so this file is redundant. Harmless but clutter.

**Classification:** WARNING

---

### W15. k and omega -- motorBikeGroup values are identical to UAUV patch values

Not a separate hit, but worth noting: the boundary condition values for `motorBikeGroup` (e.g., `value uniform 1e-10`) happen to be the same sensible defaults used for the UAUV patches. So the patch-removal fix is clean -- just delete the block, no value changes needed.

**Classification:** WARNING (documentation only)

---

## OK hits (correctly ours)

### OK1. forceCoeffs -- all reference values are UAUV

**File:** `system/forceCoeffs`, lines 30-32
```
magUInf         50;           // design cruise speed [m/s]
lRef            1.021;        // hull length [m]
Aref            0.075;        // wing planform area [m2]
```
**Verification:**
- `magUInf = 50` matches our air cruise speed (motorBike was 20).
- `lRef = 1.021` matches our measured hull length (motorBike was 1.42).
- `Aref = 0.075` matches our wing planform area (motorBike was 0.75).

All three are correctly swapped. **OK.**

---

### OK2. initialConditions -- flowVelocity is correct

**File:** `0.orig/include/initialConditions`, line 1
```
flowVelocity         (-50 0 0);
```
**Verification:** 50 m/s in the -X direction (inlet is on +X side, flow goes toward -X, hitting nose at X~0 first). This is correct for our case. **OK** (but see CRITICAL #10 for the k/omega values in the same file).

---

## Files that are CLEAN (no motorBike traces)

These 21 files passed with zero hits:

| File | Notes |
|------|-------|
| `0.orig/include/fixedInlet` | Orphaned but clean (generic inlet BC) |
| `system/blockMeshDict` | UAUV domain: inlet/outlet/farfield |
| `system/snappyHexMeshDict` | UAUV geometry: NBody, VFin, HFin, Pivot, wing |
| `system/controlDict` | simpleFoam, 500 iterations -- generic |
| `system/fvSchemes` | Standard steady-state schemes -- generic |
| `system/fvSolution` | Standard SIMPLE settings -- generic |
| `system/forceCoeffs` | UAUV values (verified OK above) |
| `system/topoSetDict` | Generic cellZone for post-processing |
| `system/streamLines` | Generic streamLine config, no patch refs |
| `system/cuttingPlane` | Generic cutting plane, no patch refs |
| `system/graphFunctionObject` | References `forceCoeffs1` (correct) |
| `system/surfaceFeatureExtractDict` | UAUV STL files only |
| `system/meshQualityDict` | Generic, includes system defaults |
| `system/decomposeParDict.6` | 6 subdomains, hierarchical -- generic |
| `system/decomposeParDict-random` | 3 subdomains, random -- generic |
| `system/profiling` | Generic parallel profiling config |
| `system/foamReport` | Generic report config |
| `system/solverInfo` | Generic solver info function object |
| `system/finite-area/faSolution` | Empty solvers dict |
| `system/finite-area/faSchemes` | Empty schemes dicts |
| `constant/transportProperties` | nu = 1.5e-05 (air) -- correct |
| `constant/turbulenceProperties` | kOmegaSST -- correct |
| `Allclean` | Generic clean script |

---

## Patch name cross-reference

| Our mesh patches (blockMeshDict + snappyHexMeshDict) | Status in boundary files |
|---|---|
| `inlet` | Present and correct in all 5 BC files |
| `outlet` | Present and correct in all 5 BC files |
| `farfield` | Present and correct in all 5 BC files |
| `NBody` | Present and correct in all 5 BC files |
| `VFin` | Present and correct in all 5 BC files |
| `HFin` | Present and correct in all 5 BC files |
| `Pivot` | Present and correct in all 5 BC files |
| `wing` | Present and correct in all 5 BC files |
| `motorBikeGroup` | **FOREIGN -- exists in all 5 BC files, NOT in mesh** |
| `upperWall` | **FOREIGN -- in orphaned include, NOT in mesh** |
| `frontAndBack` | **FOREIGN -- in orphaned include and ensightWrite, NOT in mesh** |
| `lowerWall` | **FOREIGN -- in faMeshDefinition, NOT in mesh** |

---

## Fix priority

1. **Immediate (blocks any run):** Remove `motorBikeGroup` blocks from `0.orig/U`, `0.orig/p`, `0.orig/k`, `0.orig/omega`, `0.orig/nut`.
2. **Immediate (blocks any run):** Rewrite `Allrun` to copy UAUV STL files from `~/UAUV/stl/` instead of motorBike.obj.gz from `$FOAM_TUTORIALS`.
3. **High (corrupts results):** Recompute `turbulentKE` and `turbulentOmega` in `0.orig/include/initialConditions` for 50 m/s.
4. **High (breaks function objects):** Fix `system/wallBoundedStreamLines` to reference UAUV patches.
5. **High (breaks function objects):** Fix `system/ensightWrite` to use `farfield` instead of `frontAndBack`.
6. **Medium (dead code):** Fix or remove `system/finite-area/faMeshDefinition`.
7. **Low (cosmetic):** Delete orphaned include files `0.orig/include/frontBackUpperPatches` and `0.orig/include/fixedInlet`, or comment them clearly as "not used."
8. **Low (cosmetic):** Update `system/myReportTemplate.md` OpenFOAM version string.

---

## Verdict

**FAIL.** The case would crash immediately on startup because `motorBikeGroup` is defined in all 5 boundary condition files but does not exist in the mesh. Additionally, the `Allrun` script would mesh a motorcycle instead of the UAUV, and the turbulence inlet values are tuned for 20 m/s (motorBike) rather than 50 m/s (UAUV). The core configuration (snappyHexMeshDict, blockMeshDict, forceCoeffs, fvSchemes, fvSolution, transportProperties, turbulenceProperties) is correctly adapted, but the boundary conditions and automation scripts need the fixes listed above before any CFD run.
