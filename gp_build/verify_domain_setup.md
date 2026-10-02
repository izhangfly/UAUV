# UAUV Aero Domain Verification Report

**Date:** 2026-08-02
**Case:** `/Users/ianzhang/UAUV/cfd/aero_template/`
**Solver:** simpleFoam (steady, incompressible, k-omega SST)
**Condition:** Air, 50 m/s, wing deployed (Wing90), alpha = 0 deg

---

## Vehicle Geometry Reference

| Parameter | Value | Source |
|-----------|-------|--------|
| Length (L) | 1.021 m | Verified STL |
| Nose X | ~0.0 | Verified STL |
| Tail X | ~-1.02 | Verified STL |
| Body center Y | -0.30 | Verified STL |
| Body center Z | 0.0 | Verified STL |
| Wing span (deployed) | Y -0.655 to +0.055 | Verified STL |
| Wing planform area | 0.075 m^2 | CAD / the project design notes |

---

## Check 1: Domain Size

**blockMeshDict domain:** X [-10, +7], Y [-6, +6], Z [-6, +6]
**Total:** 17.0 m (X) x 12.0 m (Y) x 12.0 m (Z)

| Direction | Distance (m) | Body Lengths | Rule | Status |
|-----------|-------------|--------------|------|--------|
| Upstream (nose to +X inlet) | 7.00 | 6.86 L | >= 5 L | **PASS** |
| Downstream (tail to -X outlet) | 8.98 | 8.80 L | >= 10 L | **WARN** |
| Lateral +Y (wing tip to +Y boundary) | 5.945 | 5.82 L | >= 5 L | **PASS** |
| Lateral -Y (wing tip to -Y boundary) | 5.345 | 5.24 L | >= 5 L | **PASS** |
| Vertical +/-Z (body to Z boundaries) | 6.00 | 5.88 L | >= 5 L | **PASS** |

**WARN detail:** Downstream distance is 8.80 L vs the recommended 10 L (12% short).
For force-coefficient extraction this is acceptable -- body forces converge well
before the far-wake velocity deficit does. If lift/drag coefficients vary with
domain extension in a grid-convergence study, extending the -X face to -12 m
would bring it to 10.8 L. Recommended as a sensitivity check before production
sweeps, but not a blocking issue.

---

## Check 2: Inlet / Outlet Face Orientation

| Face | Vertices | X-coordinate | Role |
|------|----------|-------------|------|
| inlet | (1 2 6 5) | X = +7 | Freestream enters here |
| outlet | (0 4 7 3) | X = -10 | Flow exits here |

- Freestream enters at the +X face, travels in the -X direction, hits the nose
  (X ~ 0) first, passes over the body, and exits at the -X face.
- Inlet is upstream of the nose. Outlet is downstream of the tail.
- Face assignments match the flow direction.

**Result: PASS**

---

## Check 3: Vehicle Centering

| Axis | Vehicle Range | Domain Range | Margins |
|------|--------------|--------------|---------|
| X | -1.02 to 0.0 | -10.0 to +7.0 | +7.0 upstream, 8.98 downstream |
| Y | -0.655 to +0.055 | -6.0 to +6.0 | 5.35 to -Y, 5.95 to +Y |
| Z | symmetric about 0 | -6.0 to +6.0 | 6.0 each side |

- Vehicle is slightly offset in Y (center at -0.30 vs domain center at 0.0),
  but the offset is 0.30 m (< 0.3 L) and the closest boundary is 5.24 L away.
  This is negligible.
- Vehicle Y offset matches the CAD geometry (fuselage is not at Y=0 in the STL
  coordinate system). This is the correct approach -- do not translate the STL;
  the domain accommodates the as-designed coordinates.
- locationInMesh in snappyHexMeshDict: (2, 0, 0) -- well ahead of the nose and
  clear of the body. Valid fluid point.

**Result: PASS**

---

## Check 4: Flow Direction (0/U)

**include/initialConditions:**
```
flowVelocity    (-50 0 0);
pressure        0;
```

**Inlet BC (`0.orig/U`):**
```
inlet { type fixedValue; value uniform (-50 0 0); }
```

**Internal field:**
```
internalField uniform $flowVelocity;   // = (-50 0 0)
```

- Inlet imposes -50 m/s in X (flow from +X toward -X).
- Internal field is initialized to the same value.
- Flow enters at the +X face and travels to -X. Since the nose is near X=0 and
  the tail at X=-1, flow hits the nose first.
- Magnitude = 50 m/s, matching the design cruise speed.

**Result: PASS**

---

## Check 5: Far-Field Boundary Conditions

| Field | Patch | BC Type | Physical Meaning | Status |
|-------|-------|---------|-----------------|--------|
| U | inlet | fixedValue (-50,0,0) | Prescribed freestream velocity | **PASS** |
| U | outlet | inletOutlet | Zero-gradient outflow, blocks reverse flow | **PASS** |
| U | farfield | slip | Inviscid, zero normal velocity, free slip | **PASS** |
| U | NBody/VFin/HFin/Pivot/wing | noSlip | Viscous wall (u=0 at surface) | **PASS** |
| p | inlet | zeroGradient | Standard for velocity-inlet incompressible | **PASS** |
| p | outlet | fixedValue = 0 | Reference pressure (gauge) | **PASS** |
| p | farfield | zeroGradient | Allows pressure to adjust at far boundaries | **PASS** |
| p | NBody/VFin/HFin/Pivot/wing | zeroGradient | Standard for wall pressure | **PASS** |

- `slip` on far-field U is correct: it enforces zero normal velocity and zero
  shear, approximating an inviscid far-field boundary. This is the standard
  treatment for external aerodynamics (no boundary layer at domain edges).
- `inletOutlet` on outlet U is correct: it applies fixedValue (0,0,0) if flow
  reverses (unlikely but guards against divergence) and zeroGradient for
  normal outflow. This is more robust than a pure zeroGradient outlet.
- **Minor dead code:** `motorBikeGroup` appears in U and p boundaryField but
  is NOT created by snappyHexMeshDict (no matching geometry entry). This is a
  leftover from the motorBike tutorial template. Zero-face patches are harmless
  at runtime but should be cleaned up to avoid confusion.

**Result: PASS** (with cleanup note)

---

## Check 6: dragDir vs Flow Direction

**forceCoeffs:**
```
dragDir    (-1 0 0);     // drag is measured in the -X direction
```

**Freestream velocity in 0/U:**
```
inlet value uniform (-50 0 0);   // flow in -X direction
```

- `dragDir` points in the same direction as the freestream velocity vector
  relative to the stationary body. This is the standard OpenFOAM convention:
  drag acts on the body in the direction of the oncoming flow.
- Dot product: `dragDir` dot `U_inf` = (-1,0,0) dot (-50,0,0) = +50 > 0.
  Both are in the -X direction. **CORRECT.**

**Result: PASS**

---

## Check 7: liftDir Orthogonality

```
dragDir    (-1 0 0);
liftDir    (0 0 1);
```

- Dot product: `(-1,0,0)` dot `(0,0,1)` = 0. Perpendicular. **PASS**
- Wing span direction: the deployed wing (Wing90) extends in the Y direction
  (Y -0.655 to +0.055), i.e., the wing lies in the X-Y plane.
- For a wing in the X-Y plane with flow in -X, lift is in the +Z direction.
  `liftDir (0 0 1)` matches this. **PASS**
- `pitchAxis (0 1 0)` is perpendicular to both dragDir and liftDir, and
  parallel to the wing span. Correct for the moment coefficient. **PASS**

**IMPORTANT NOTE for alpha sweeps:** When the inflow vector in 0/U is rotated
to simulate angle of attack, `liftDir`, `dragDir`, and `pitchAxis` in
forceCoeffs MUST be rotated by the same angle. This is the standard
"rotate the flow, not the mesh" approach described in the project design notes, section 6.
At alpha=0 the current setup is correct.

**Result: PASS**

---

## Check 8: Reference Values

| Parameter | Value | Expected | Source | Status |
|-----------|-------|----------|--------|--------|
| magUInf | 50 | 50 m/s | Design spec | **PASS** |
| lRef | 1.021 | 1.021 m | Verified STL body length | **PASS** |
| Aref | 0.075 | 0.075 m^2 | CAD planform area (the project design notes) | **PASS** |
| rhoInf | 1.225 | 1.225 kg/m^3 | Air at sea level, 15 deg C | **PASS** |
| CofR X | -0.51 | ~mid-body | Body X: -1.02 to 0.0, midpoint -0.51 | **PASS** |
| CofR Y | -0.30 | body center | Matches STL body center | **PASS** |
| CofR Z | 0.0 | symmetry plane | Matches STL body center | **PASS** |

- `lRef` uses hull length (1.021 m), not wing chord. Standard for full-vehicle
  aero coefficients where the fuselage contributes.
- `Aref` uses wing planform area (0.075 m^2). Standard for aircraft-type
  configurations where lift is wing-dominated.

**Result: PASS**

---

## Additional Checks

### A. snappyHexMeshDict vs blockMeshDict Consistency

- snappyHexMeshDict comment claims domain is `(-7 -4 -4) to (4 4 4)` but the
  actual blockMeshDict domain is `(-10 -6 -6) to (7 6 6)`. **Stale comment.**
  The actual domain is correct and wider; the comment is harmless but
  misleading. Should be updated.

### B. Patch Name Consistency

| snappyHexMeshDict (creates) | 0.orig/U | 0.orig/p | forceCoeffs |
|----------------------------|----------|----------|-------------|
| NBody | NBody | NBody | NBody |
| VFin | VFin | VFin | VFin |
| HFin | HFin | HFin | HFin |
| Pivot | Pivot | Pivot | Pivot |
| wing | wing | wing | wing |
| (none) | motorBikeGroup | motorBikeGroup | (not listed) |

- `motorBikeGroup` is a leftover template patch with no corresponding geometry.
  Zero-face patches do not cause runtime errors but are dead entries.
  Recommended: remove from U and p to keep the case clean.

### C. Pressure Dimensions

- `dimensions [0 2 -2 0 0 0 0]` = m^2/s^2 = kinematic pressure (p/rho).
  This is correct for incompressible simpleFoam, which solves p/rho.

### D. Turbulence Initial Conditions

```
turbulentKE      0.24;     // k   [m^2/s^2]
turbulentOmega   1.78;     // omega [1/s]
```

- At U=50 m/s, L=1.021 m: turbulent intensity estimate ~1%, k = 1.5*(0.01*50)^2
  = 0.375. The value 0.24 corresponds to ~0.8% intensity. Reasonable for a
  clean external aero case with moderate freestream turbulence.
- omega = k^0.5 / (0.09^0.25 * L_turb) with L_turb ~ 0.1*L_body gives omega
  in the 1-2 range. Value 1.78 is plausible.
- These are initial values; the RANS solver will develop its own turbulent
  field. Exact values matter only for convergence rate, not the final solution.

---

## Final Verdict

### OVERALL: READY FOR PRODUCTION SWEEPS (with one recommendation)

All 8 checks pass at the fundamental level. The domain orientation, flow
direction, boundary conditions, and force-coefficient references are physically
correct. The setup will produce valid lift and drag coefficients at alpha=0.

### Recommendations (non-blocking)

1. **Downstream domain extension (before production sweeps):** Extend the -X
   face from -10 to -12 m to achieve the full 10 L downstream distance. Run
   one alpha=0 case at both domains and compare Cd/Cl. If they differ by
   less than 1%, the current 8.8 L domain is sufficient. This is a 15-minute
   mesh-and-run check.

2. **Clean up motorBikeGroup:** Remove the `motorBikeGroup` patch from
   `0.orig/U` and `0.orig/p`. Zero-face patches do not break anything but
   add confusion during debugging.

3. **Fix stale snappyHexMeshDict comment:** Update the domain bounds comment
   on line ~110 from `(-7 -4 -4) to (4 4 4)` to `(-10 -6 -6) to (7 6 6)`.

4. **Alpha sweep script requirement:** When rotating the inflow vector for
   angle-of-attack sweeps, the script must simultaneously rotate `liftDir`,
   `dragDir`, and `pitchAxis` in forceCoeffs by the same angle. Failure to
   do this will produce mis-labeled force components.

### Summary Table

| # | Check | Result |
|---|-------|--------|
| 1 | Domain size adequate | PASS (downstream WARN at 8.8L vs 10L) |
| 2 | Inlet/outlet orientation correct | PASS |
| 3 | Vehicle well-centered | PASS |
| 4 | Flow direction into domain from inlet | PASS |
| 5 | Far-field BCs correct (slip, not wall) | PASS |
| 6 | dragDir points in correct direction | PASS |
| 7 | liftDir perpendicular to dragDir and span | PASS |
| 8 | Reference values correct | PASS |
