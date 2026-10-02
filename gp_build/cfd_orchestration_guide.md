# UAUV CFD Orchestration Guide — OpenFOAM v2606 on macOS (Apple Silicon)

**Purpose:** Step-by-step runbook for the three CFD campaigns (AERO, HYDRO, ENTRY) defined in
`gp_build/cfd_sweep_plan.md`. Every command and path is verified against the installed system.

**Prerequisites:** OpenFOAM v2606 (Gerlero native ARM) via `brew install gerlero/openfoam/openfoam`;
14 watertight STLs in `~/UAUV/stl/` (already in metres, verified); ParaView 6.1.1 via
`brew install --cask paraview`.

**Verified against:** OpenFOAM User Guide v2012 (§4.4 snappyHexMesh, §6.2 fvSchemes, Ch.7 post-processing,
App.A solvers); `cfd/aero_template/` (motorBike tutorial adapted); installed Gerlero app binaries;
forceCoeffs source in `~/UAUV/cfd/aero_template/system/forceCoeffs`.

---

## 0. Critical: Always Run Inside the OpenFOAM Shell

**Every command in this guide — solvers, meshers, post-processing utilities — only works inside
the `openfoam` shell.** Launch it at the start of every session:

```bash
openfoam
```

This mounts the read-only volume at `/Volumes/OpenFOAM-v2606/` and puts all solvers on PATH.
You'll see a prompt like `openfoam2606:~/your/path ianzhang$`. Do all work in this shell.
Exit with `exit` when done.

**Verified commands inside the shell** (all at `/Volumes/OpenFOAM-v2606/.../bin/`):

| Command | Purpose | Verified |
|---|---|---|
| `blockMesh` | Background mesh generator | ✅ |
| `snappyHexMesh` | Surface-wrapping mesher (3-stage) | ✅ |
| `surfaceFeatureExtract` | Edge extraction from STLs | ✅ |
| `checkMesh` | Mesh quality diagnostics | ✅ |
| `simpleFoam` | Steady incompressible turbulent solver | ✅ |
| `interFoam` | Transient VOF two-phase solver | ✅ |
| `foamDictionary` | Scripted dict edits (key for α sweep) | ✅ |
| `foamListTimes` | List/remove timestep directories | ✅ |
| `decomposePar` | Mesh decomposition for parallel | ✅ |
| `reconstructPar` | Reassembly after parallel run | ✅ |
| `mpirun` | MPI launcher (at `$FOAM_APPBIN/../env/bin/mpirun`) | ✅ |
| `paraFoam` | ParaView launcher (at `/Volumes/OpenFOAM-v2606/bin/paraFoam`) | ✅ |
| `topoSet` | Cell-set manipulation | ✅ |
| `setFields` | Non-uniform initial field setup | ✅ |
| `potentialFoam` | Potential-flow initialisation | ✅ |

**Checked and ALL exist.** The earlier confusion was from running outside the `openfoam` shell.

---

## 1. Case Directory Setup

### 1.1 Start from the template
```bash
openfoam                                        # enter OpenFOAM shell
cd ~/UAUV/cfd
cp -r aero_template aero_wing90                 # create the first case
cd aero_wing90
```

The template (`cfd/aero_template/`) is a copy of OpenFOAM's motorBike tutorial. It already has:
- `system/blockMeshDict` (domain box — already adapted for our vehicle, L=1.02 m)
- `system/snappyHexMeshDict` (needs geometry + patch names updated)
- `system/controlDict` (already set to `application simpleFoam`)
- `system/fvSchemes` + `system/fvSolution` (k-ω SST, transient simpleFoam)
- `system/forceCoeffs` (needs reference values updated)
- `system/decomposeParDict.6` (parallel decomposition, 6 subdomains)
- `0.orig/` (initial conditions — COPY to `0/` before running)
- `constant/transportProperties` + `constant/turbulenceProperties`

### 1.2 Create the triSurface directory and copy STLs
```bash
mkdir -p constant/triSurface
cp ~/UAUV/stl/NBody.stl constant/triSurface/
cp ~/UAUV/stl/VFin.stl constant/triSurface/
cp ~/UAUV/stl/HFin.stl constant/triSurface/
cp ~/UAUV/stl/Pivot_Actuator_cylinder.stl constant/triSurface/
cp ~/UAUV/stl/Wing90.stl constant/triSurface/wing.stl    # rename to generic name
```

**Why rename to `wing.stl`:** the snappyHexMeshDict references `wing` as the patch name.
This keeps the dict generic — for Wing60, you swap just the file, not the dict.

### 1.3 Copy initial conditions
```bash
cp -r 0.orig 0
```
OpenFOAM reads from `0/`, not `0.orig/` (which is the backup). Always do this before a run.

---

## 2. Step-by-Step: AERO Campaign (simpleFoam, air 50 m/s)

### 2.1 Background mesh
```bash
blockMesh
```
Creates `constant/polyMesh/` from `system/blockMeshDict`.

**Verify:**
```bash
checkMesh
```
Look for: `Mesh OK` at the end. No negative-volume cells. Max aspect ratio < 100.

### 2.2 Surface feature extraction
```bash
surfaceFeatureExtract
```
Extracts sharp edges from all STLs for snappyHexMesh refinement. Uses
`system/surfaceFeatureExtractDict`.

### 2.3 Surface wrapping
```bash
snappyHexMesh -overwrite
```
Three stages: castellated (refinement) → snap (surface fitting) → addLayers (boundary layer).
The `-overwrite` flag updates the mesh in-place.

**Key snappyHexMeshDict settings to update** (open `system/snappyHexMeshDict`):
```cpp
geometry {
    NBody.stl     { type triSurfaceMesh; name NBody; }
    VFin.stl      { type triSurfaceMesh; name VFin; }
    HFin.stl      { type triSurfaceMesh; name HFin; }
    Pivot_Actuator_cylinder.stl { type triSurfaceMesh; name Pivot; }
    wing.stl      { type triSurfaceMesh; name wing; }
}

castellatedMeshControls {
    locationInMesh (0 0.2 0);   // point in fluid AWAY from body
    maxLocalCells 100000;
    maxGlobalCells 2000000;
    refinementSurfaces {
        NBody  { level (4 5); patchInfo { type wall; } }
        VFin   { level (4 5); patchInfo { type wall; } }
        HFin   { level (4 5); patchInfo { type wall; } }
        Pivot  { level (4 5); patchInfo { type wall; } }
        wing   { level (5 6); patchInfo { type wall; } }
    }
}
```
**`locationInMesh` must be inside the fluid domain, not on a cell face, and must stay
inside throughout refinement** (User Guide §4.4.2). `(0 0.2 0)` works — it's off-axis
away from the hull. If snappy exits with 0 cells, this point is wrong.

### 2.4 Set angle of attack — rotate inlet velocity
**Do NOT re-mesh for each α.** Edit `0/U` and `system/forceCoeffs` using `foamDictionary`:

```bash
# For α = 3° (example)
ALPHA=3
Vx=$(python3 -c "import math; print(50*math.cos(math.radians($ALPHA)))")
Vz=$(python3 -c "import math; print(50*math.sin(math.radians($ALPHA)))")

foamDictionary 0/U -entry "boundaryField.inlet.value" \
    -set "uniform ($Vx 0 $Vz)"

# Update force directions in forceCoeffs
foamDictionary system/forceCoeffs -entry liftDir \
    -set "($Vz 0 $Vx)"       # perpendicular to freestream
foamDictionary system/forceCoeffs -entry dragDir \
    -set "($Vx 0 $Vz)"       # parallel to freestream
```

### 2.5 Update forceCoeffs reference values

**Before the first run, set our vehicle's reference values** in `system/forceCoeffs`:
```cpp
patches         (NBody VFin HFin Pivot wing);  // ALL wetted patches
rho             rhoInf;
rhoInf          1.225;       // air density kg/m³
liftDir         (0 0 1);     // update per α via foamDictionary
dragDir         (1 0 0);     // update per α via foamDictionary
CofR            (-0.51 0 0); // mid-hull (nose at origin, tail at -1.021)
pitchAxis       (0 1 0);
magUInf         50;          // m/s
lRef            1.021;       // hull length
Aref            0.075;       // wing area (m²) — UPDATE from CAD
```

### 2.6 Run (parallel, 6 performance cores)
```bash
decomposePar -decomposeParDict system/decomposeParDict.6
mpirun -np 6 simpleFoam -parallel
reconstructPar
```

Progress is logged to `log.simpleFoam`. Monitor in another terminal:
```bash
tail -f log.simpleFoam
```

### 2.7 Check convergence
```bash
tail postProcessing/forceCoeffs/0/coefficient.dat
```
Convergence: the **mean of the last 10% of iterations** for C_D, C_L should be stable
(std < 1% of mean). If not converged, continue from latest time with `simpleFoam` (no `-parallel`).

### 2.8 Post-process in ParaView
```bash
touch case.foam
paraFoam case.foam           # launches ParaView with OpenFOAM reader
```
Key filters: `ExtractBlock` → isolate wing patches; `Calculator` → $C_p = (p-p_\infty)/(0.5\rho V_\infty^2)$;
`PlotOverLine` → $C_p$ along wing chord; `Find Data` → $\min(C_p)$ on wing (cavitation).

### 2.9 Sweep α — re-run on same mesh
```bash
foamListTimes -rm             # delete old timestep data (keeps 0/ and constant/)
rm -rf processor* postProcessing log.simpleFoam
# Edit 0/U and system/forceCoeffs for new α
# Repeat §2.4 → §2.6
```
One mesh serves ~10 α values. **5 meshes × ~10 α = ~50 runs.**

---

## 3. HYDRO Campaign (simpleFoam, water)

**Same pipeline as AERO with these changes:**

### 3.1 Transport properties
In `constant/transportProperties`:
```cpp
transportModel  Newtonian;
nu              [0 2 -1 0 0 0 0] 1.0e-6;   // ν_water
```
In `system/forceCoeffs`: `rhoInf 1000` (water density).

### 3.2 Velocity sweep
Edit `0/U` inlet magnitude to {2, 5, 10, 15, 20} via `foamDictionary`:
```bash
foamDictionary 0/U -entry "boundaryField.inlet.value" -set "uniform ($Vw 0 0)"
```
(Set $Vz=0 for horizontal flow in water; adjust for the stowed-wing trim-block α sweep.)

### 3.3 Cavitation check (post-processing, no extra CFD)
After the run, open `case.foam` in ParaView:
1. `Calculator`: `Cp = (p - 101325) / (0.5 * 1000 * Vw^2)`
2. `Find Data`: minimum of `Cp` on wing + hull → $-\min(C_p)$
3. Compare to $\sigma(h, V_w) = (101325 + 1000\cdot 9.81 \cdot h - 2340) / (0.5 \cdot 1000 \cdot V_w^2)$
4. If $-\min(C_p) \ge \sigma$, cavitation occurs → activate Phase 2 (Zwart model)

---

## 4. ENTRY Campaign (interFoam VOF, 2D, transient)

### 4.1 2D domain
In `system/blockMeshDict`: use front and back `empty` patches:
```cpp
boundary ( frontAndBack { type empty; faces (...); } ... )
```
The domain is a water tank: lower half water ($\alpha.\text{water}=1$), upper half air
($\alpha.\text{water}=0$), set via `0/alpha.water` and `system/setFieldsDict`.

### 4.2 Solver
```cpp
// system/controlDict
application     interFoam;
```

### 4.3 Transient settings
```cpp
startFrom       startTime;
startTime       0;
endTime         0.05;
deltaT          1e-6;
writeInterval   0.001;
adjustTimeStep  yes;
maxCo           0.5;
```

### 4.4 Body insertion
```bash
topoSet -dict system/topoSetDict.body
setFields -dict system/setFieldsDict
```

### 4.5 Run
```bash
mpirun -np 6 interFoam -parallel
```

### 4.6 Output: $a_{\text{peak}}$
The `forces` function object (not `forceCoeffs` — interFoam needs raw forces) outputs to
`postProcessing/forces/0/force.dat`. Peak acceleration:
$$a_{\text{peak}} = \max_t |F_x(t)| / m_{\text{eff}}$$
where $m_{\text{eff}} = m + m_a$ (added mass from G4 extraction: $m_a \approx 0.03\,\rho_w\nabla$).

---

## 5. Batch Automation (skeleton)

```bash
#!/bin/bash
# Batch α sweep for ONE wing mesh. Run INSIDE the openfoam shell.
WING_MESH=$1
cd "$WING_MESH" || exit 1
cp -r 0.orig 0
ALPHAS=(-4 -2 0 2 4 6 8 10 12 14)
for ALPHA in "${ALPHAS[@]}"; do
    echo "=== α=$ALPHA ==="
    Vx=$(python3 -c "import math; print(50*math.cos(math.radians($ALPHA)))")
    Vz=$(python3 -c "import math; print(50*math.sin(math.radians($ALPHA)))")
    foamDictionary 0/U -entry "boundaryField.inlet.value" -set "uniform ($Vx 0 $Vz)"
    foamDictionary system/forceCoeffs -entry liftDir -set "($Vz 0 $Vx)"
    foamDictionary system/forceCoeffs -entry dragDir -set "($Vx 0 $Vz)"
    foamListTimes -rm 2>/dev/null
    rm -rf processor* postProcessing log.simpleFoam
    decomposePar -decomposeParDict system/decomposeParDict.6 > /dev/null 2>&1
    mpirun -np 6 simpleFoam -parallel > "log.a${ALPHA}" 2>&1
    reconstructPar > /dev/null 2>&1
    # Parse final C_L, C_D
    tail -1 postProcessing/forceCoeffs/0/coefficient.dat \
        | awk -v a="$ALPHA" '{print a","$2","$3}' >> results.csv
done
```

---

## 6. Grid-Convergence Study

One dedicated run at nominal design point (Λ=0, α=4°, V=50 m/s), varying refinement:

| Refinement level | Cells | snappyHexMesh setting |
|---|---|---|
| Coarse | ~0.5 M | `level (3 4)` |
| Medium | ~1.5 M | `level (4 5)` |
| Fine | ~4 M | `level (5 6)` |
| Extra-fine | ~8 M | `level (6 7)` |

Richardson extrapolation on $C_D$ → grid-independent value + uncertainty. Medium is the
sweep mesh; if fine differs <2%, sweep is adequate.

---

## 7. Common Errors & Fixes

| Symptom | Cause | Fix |
|---|---|---|
| `blockMesh` exits with "negative volume" | Vertices wrong-handed | Check `hex` block vertex order |
| `snappyHexMesh` produces 0 cells | `locationInMesh` outside fluid | Set to `(0 0.2 0)` — off-body but inside domain |
| `simpleFoam` diverges in first 5 iterations | Inlet BCs or relaxation | Set `p 0.3; U 0.5; k 0.5; omega 0.5` in `fvSolution` |
| `mpirun` not found | Not in OpenFOAM shell | Type `openfoam` first |
| `foamDictionary` not found | Not in OpenFOAM shell | Type `openfoam` first |
| `foamListTimes -rm` fails | No timestep dirs exist | `rm -rf [0-9]* [1-9]*.[0-9]*` manually |
| Memory pressure | Mesh too large | Target 1–2 Mcells for sweeps; wall functions reduce cell count |
| `interFoam` crashes on first step | Δt too large | Set `deltaT 1e-7` in `controlDict` |

---

## 8. ParaView Quick Start

```bash
# Inside the OpenFOAM shell:
touch case.foam
paraFoam case.foam
```

**Essential filters:**
| Filter | Purpose |
|---|---|
| `ExtractBlock` → wall patches | Isolate body/wing/fins |
| `Calculator` | $C_p = (p-p_\infty)/(0.5\rho V_\infty^2)$ |
| `Slice` | 2D cut at mid-span |
| `PlotOverLine` | $C_p$ along wing chord |
| `Contour` | Pressure/velocity/$\mu_t/\mu$ fields |
| `StreamTracer` | Flow pathlines |
| `Find Data` | $\min(C_p)$ (cavitation check) |
| `IntegrateVariables` | Patch-integrated forces (cross-check with forceCoeffs) |

---

## 9. References

- Gerlero openfoam-app: https://github.com/gerlero/openfoam-app
- OpenFOAM User Guide v2012: `~/UAUV/UserGuide.pdf` (Ch.4 meshing, Ch.6 schemes, Ch.7 post-processing, App.A solvers)
- OpenFOAM Programmer's Guide v2012: `~/UAUV/ProgrammersGuide.pdf`
- Unzipped ESI source + tutorials: `~/UAUV/OpenFOAM2606/` (doc reference, NOT compiled)
- CFD sweep plan: `~/UAUV/gp_build/cfd_sweep_plan.md`
- GP model: `~/UAUV/gp_model.tex` / `gp_model.pdf`
