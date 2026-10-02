#!/bin/bash
# ENTRY campaign batch — 2D interFoam VOF, body-fixed frame
# 5 speeds × 5 angles × 3 masses = 75 runs. ~5-10 min/run → ~6-12 hours.
# MUST run inside openfoam shell with: source batch_entry_fixed.sh
# set -e disabled

TEMPLATE=/Users/ianzhang/UAUV/cfd/entry_template
RUNS=/Users/ianzhang/UAUV/cfd/entry_runs
DB=/Users/ianzhang/UAUV/cfd/database/entry_results.csv
STLGEN=/Users/ianzhang/UAUV/cfd/entry_template/create_nose_stl.py
NP=6

V_ENTRY=(70 60 50 40 30)
THETA=(-75 -60 -45 -30 -15)   # angle from horizontal, negative = descending
MASS=(3 5 8)

mkdir -p "$RUNS" "$(dirname "$DB")"
echo "case,V_entry,theta,m,a_peak_ms2,a_peak_g,status,wall_s" > "$DB"
TOTAL=$((${#V_ENTRY[@]} * ${#THETA[@]} * ${#MASS[@]}))
DONE=0

for V in "${V_ENTRY[@]}"; do
  for TH in "${THETA[@]}"; do
    for M in "${MASS[@]}"; do
      DONE=$((DONE+1))
      CASE="V${V}_th$((-TH))_m${M}"
      DIR="$RUNS/$CASE"
      echo "=== [$DONE/$TOTAL] $CASE ==="
      T0=$(date +%s)

      # Build case from scratch (no reuse — clean each time)
      rm -rf "$DIR"
      cp -r "$TEMPLATE" "$DIR"
      mkdir -p "$DIR/constant/triSurface"

      # Generate STL (vertical slender ogive, tip at Z=0)
      cd "$DIR"
      python3 "$STLGEN" > /dev/null 2>&1

      # Vertical penetration: water rises at Vn = V*sin|theta| (normal-velocity governs slam).
      # endTime scales with the case so the peak is captured for slow AND fast entries.
      read Vn ENDT <<< $(python3 -c "
import math
Vn=$V*abs(math.sin(math.radians($TH)))
endt=min(0.05, max(0.004, 0.3/Vn))    # ~3 diameters of penetration
print(round(Vn,6), round(endt,6))
")

      # Water moves straight up at Vn (Ux=0)
      python3 -c "
u=open('0.orig/U').read()
u=u.replace('\$U_x 0 \$U_z', '0 0 $Vn')
open('0.orig/U','w').write(u)
"
      # Per-case endTime + write only the final field
      foamDictionary system/controlDict -entry endTime       -set "$ENDT"     > /dev/null 2>&1
      foamDictionary system/controlDict -entry writeInterval  -set "$ENDT"     > /dev/null 2>&1

      # Mesh
      blockMesh > log.blockMesh 2>&1
      surfaceFeatureExtract > log.sfe 2>&1
      snappyHexMesh -overwrite > log.sHM 2>&1
      if ! grep -q "Finished meshing without any errors" log.sHM; then
        T1=$(date +%s)
        echo "$CASE,$V,$TH,$M,nan,nan,mesh_fail,$((T1-T0))" >> "$DB"
        cd /Users/ianzhang/UAUV/cfd; continue
      fi

      # Set up 0/ — copy fields over snappyHexMesh output (don't rm -rf 0)
      rm -f 0/cellLevel 0/pointLevel 0/nSurfaceLayers 0/thickness 0/thicknessFraction
      cp 0.orig/U 0.orig/p_rgh 0.orig/alpha.water 0/
      rm -rf processor*

      # Set water phase (alpha=1 below Z=0; body sits in air above)
      setFields > log.setFields 2>&1 || true

      # Run
      decomposePar -decomposeParDict system/decomposeParDict.6 -force > /dev/null 2>&1
      mpirun -np $NP interFoam -parallel > log.interFoam 2>&1
      reconstructPar > /dev/null 2>&1

      # Extract peak force. Body starts in AIR (tip touching surface), so force rises
      # from ~0 as the surface wets the nose — the max is the PHYSICAL slam, not a t=0
      # artifact. Skip the first 1% of steps as a guard. Report a_peak and time-to-peak.
      FF="postProcessing/bodyForces/0/force.dat"
      read a_peak a_g t_peak st <<< $(python3 -c "
import math
try:
  rows=[l.split() for l in open('$FF') if not l.startswith('#') and l.strip()]
  rows=[r for r in rows if len(r)>=7]
  skip=max(3, len(rows)//100)          # ignore initial numerical transient
  fmax=0.0; tmax=0.0
  for r in rows[skip:]:
    t=float(r[0]); Fx=float(r[1])+float(r[4]); Fz=float(r[3])+float(r[6])
    F=math.sqrt(Fx*Fx+Fz*Fz)
    if F>fmax: fmax=F; tmax=t
  a=fmax/$M
  print('%.6g %.6g %.6g ok' % (a, a/9.81, tmax))
except Exception as e:
  print('nan nan nan no_forces')
")
      [ -f "$FF" ] || { a_peak=nan; a_g=nan; t_peak=nan; st=no_forces; }
      T1=$(date +%s); DT=$((T1-T0))
      echo "  a_peak=$a_peak m/s² ($a_g g) @t=${t_peak}s  Vn=$Vn endT=$ENDT  ${DT}s $st"
      echo "$CASE,$V,$TH,$M,$a_peak,$a_g,$st,$DT" >> "$DB"
      sync
      cd /Users/ianzhang/UAUV/cfd
    done
  done
done
echo "=== ENTRY DONE $(date) | $(wc -l < $DB) rows ==="
