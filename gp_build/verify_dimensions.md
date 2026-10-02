# STL Dimension Verification — UAUV STL Files for OpenFOAM

**Date:** 2026-08-02
**Method:** Python `numpy-stl` bounding box analysis on the exported binary STL files.
**Verdict:** PASS -- all dimensions are correctly in METRES.

---

## NBody.stl (fuselage)

| Axis | Min (m) | Max (m) | Span (m) | Expected | Match |
|------|---------|---------|----------|----------|-------|
| X    | -1.020  |  0.001  | 1.021    | ~1.02    | PASS  |
| Y    | -0.350  | -0.250  | 0.100    | ~0.10    | PASS  |
| Z    | -0.050  |  0.050  | 0.100    | ~0.10    | PASS  |

- The Y offset (centered around Y = -0.30 m) is expected -- the fuselage is positioned
  below the coordinate origin in the Fusion assembly, with the wing pivot at origin.
- X length 1.021 m matches the CAD measurement of 1020 mm after `CM_TO_M = 0.01` conversion.
- Y and Z spans of 0.100 m match the 100 mm body diameter.

## Wing90.stl (wing at 90 degrees -- fully deployed)

| Axis | Min (m) | Max (m) | Span (m) | Interpretation |
|------|---------|---------|----------|----------------|
| X    | -0.595  | -0.455  | 0.140    | **Chord = 140 mm** |
| Y    | -0.655  |  0.055  | 0.710    | **Span = 710 mm** |
| Z    |  0.051  |  0.069  | 0.018    | **Thickness ~18 mm** |

- Chord (140 mm) > body diameter (100 mm) -- intentional overhang for stowed lift.
- Span (710 mm) -- this is Wing90 (deployed), so span is along Y.
- Aspect ratio = 710 / 140 = 5.07. Reasonable.
- Wing stowed length = 710 mm = 70% of body length (1021 mm). Close to the 74% estimate
  from the project design notes, section 4 under "Chord selection" (c=100 mm, b=750 mm).

## Other components (spot checks)

| File | ΔX (m) | ΔY (m) | ΔZ (m) | Interpretation |
|------|--------|--------|--------|----------------|
| VFin  | 0.050  | 0.004  | 0.200  | Vertical fin: 200 mm tall, 50 mm chord, 4 mm thick |
| HFin  | 0.050  | 0.200  | 0.004  | Horizontal fin: 200 mm span, 50 mm chord, 4 mm thick |
| Wing0 | 0.710  | 0.140  | 0.018  | Wing stowed: 710 mm along X (body axis), 140 mm chord along Y |

## Conversion chain verification

```
Fusion 360 internal units: CENTIMETRES
  → STL values in Fusion API (tessellation): e.g. 102 cm, 10 cm, 10 cm
  → fusion_export_stl.py: CM_TO_M = 0.01
  → Exported STL: 1.02 m, 0.10 m, 0.10 m
  → Verified by numpy-stl: 1.021 m, 0.100 m, 0.100 m  ✓
```

The `CM_TO_M = 0.01` conversion is correct. If Fusion exported raw cm values without
conversion, the fuselage would measure 1021 m (1 km long), which would cause immediate
and obvious failure in blockMesh, snappyHexMesh, and any CFD run. The dimensions are
clearly in metres.

## OpenFOAM compatibility

- blockMesh and snappyHexMesh have already been run on these STLs without scale errors,
  confirming correct metre-scale geometry.
- No further action required.
