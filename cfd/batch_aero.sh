#!/bin/bash
# ============================================================================
# AERO campaign — 10 wings × 10 α, air 50 m/s, simpleFoam k-ω SST.
# Output → database/aero_results.csv
# RUN INSIDE openfoam shell:  source batch_aero.sh 2>&1 | tee database/aero_batch.log
# (source, not bash — the gerlero ARM build dyld-crashes in a spawned subshell)
# ============================================================================
# set -e intentionally OFF (a dyld crash must not kill the whole sweep)

TEMPLATE=/Users/ianzhang/UAUV/cfd/aero_template
CASES=/Users/ianzhang/UAUV/cfd/cases/aero
DB=/Users/ianzhang/UAUV/cfd/database
STL=/Users/ianzhang/UAUV/stl
DECOMP=decomposeParDict.6
NP=6

# ---- AERO fluid properties (AIR) ----
RHO=1.225          # kg/m3   (forceCoeffs rhoInf, from template — not overwritten here)
NU=1.5e-5          # m2/s    (kinematic viscosity of air; must match transportProperties)
MAGUINF=50         # m/s     (fixed cruise speed)
TI=0.02            # freestream turbulence intensity (2%)
MTR=10             # target inlet eddy-viscosity ratio μt/μ

WINGS=(Wing0 Wing10 Wing20 Wing30 Wing40 Wing50 Wing60 Wing70 Wing80 Wing90)
ALPHAS=(-4 -2 0 2 4 6 8 10 12 14)

mkdir -p "$DB" "$CASES"
# Append-safe: keep existing CSV so a crash-restart RESUMES instead of wiping progress
[ -f "$DB/aero_results.csv" ] || \
  echo "wing,alpha,C_D,C_L,CmPitch,CmRoll,CmYaw,status,wall_s,notes" > "$DB/aero_results.csv"
TOTAL=$((${#WINGS[@]} * ${#ALPHAS[@]})); DONE=0

for WING in "${WINGS[@]}"; do
    CASE="$CASES/$WING"
    echo "=== $(date)  WING=$WING ==="

    # ---- Build mesh if missing; otherwise keep mesh but refresh field files ----
    if [ ! -d "$CASE/constant/polyMesh" ]; then
        rm -rf "$CASE"; cp -r "$TEMPLATE" "$CASE"
        mkdir -p "$CASE/constant/triSurface"
        for s in NBody VFin HFin Pivot_Actuator_cylinder; do cp "$STL/$s.stl" "$CASE/constant/triSurface/"; done
        cp "$STL/${WING}.stl" "$CASE/constant/triSurface/wing.stl"
        cd "$CASE"; cp -r 0.orig 0
        blockMesh > log.blockMesh 2>&1
        surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1
        snappyHexMesh -overwrite > log.snappyHexMesh 2>&1
        if ! grep -q "Finished meshing without any errors" log.snappyHexMesh; then
            echo "  !! MESH FAIL on $WING — see log.snappyHexMesh"; cd /Users/ianzhang/UAUV/cfd; continue
        fi
        echo "  mesh built OK"
    else
        cd "$CASE"
        echo "  reusing mesh — refreshing field files from template"
    fi
    # Always refresh 0.orig field files from the (fixed) template so inlet uses $internalField
    cp "$TEMPLATE/0.orig/U" "$TEMPLATE/0.orig/p" "$TEMPLATE/0.orig/k" \
       "$TEMPLATE/0.orig/omega" "$TEMPLATE/0.orig/nut" "$CASE/0.orig/" 2>/dev/null

    for ALPHA in "${ALPHAS[@]}"; do
        DONE=$((DONE+1))
        # RESUME: skip if this (wing,alpha) already completed ok
        if grep -q "^$WING,$ALPHA,.*,ok," "$DB/aero_results.csv" 2>/dev/null; then
            echo "  [$DONE/$TOTAL] $WING α=$ALPHA (done, skip)"; continue
        fi
        T0=$(date +%s)

        # ---- velocity, drag/lift directions, turbulence (all from one python call) ----
        read Vx Vz DX DZ LX LZ K OM <<< $(python3 -c "
import math
a=math.radians($ALPHA); c=math.cos(a); s=math.sin(a)
U=$MAGUINF; nu=$NU; I=$TI; mtr=$MTR
Vx=-U*c; Vz=U*s                 # flow in -X, tilt +Z for +alpha
DX=-c;   DZ=s                   # dragDir = flow unit vector
LX=s;    LZ=c                   # liftDir = span x drag, +Z at a=0 (perp to dragDir)
k=1.5*(I*U)**2                  # inlet TKE
om=k/(nu*mtr)                   # inlet omega for target mu_t/mu
print(Vx,Vz,DX,DZ,LX,LZ,k,om)
")

        # ---- write initial conditions (velocity + turbulence scale with U) ----
        {
          echo "flowVelocity ($Vx 0 $Vz);"
          echo "pressure 0;"
          echo "turbulentKE $K;"
          echo "turbulentOmega $OM;"
        } > 0.orig/include/initialConditions

        # ---- fresh forceCoeffs from template each iteration (no ;;;; accumulation) ----
        cp "$TEMPLATE/system/forceCoeffs" system/forceCoeffs
        python3 -c "
import re
t=open('system/forceCoeffs').read()
t=re.sub(r'dragDir\s+\([^)]*\);', 'dragDir         ($DX 0 $DZ);', t)
t=re.sub(r'liftDir\s+\([^)]*\);', 'liftDir         ($LX 0 $LZ);', t)
open('system/forceCoeffs','w').write(t)
"

        # ---- run ----
        rm -rf 0 processor* postProcessing; cp -r 0.orig 0
        decomposePar -decomposeParDict "system/$DECOMP" > /dev/null 2>&1
        mpirun -np $NP simpleFoam -parallel > /dev/null 2>&1
        reconstructPar > /dev/null 2>&1
        T1=$(date +%s); DT=$((T1-T0))

        # ---- parse converged coefficients (mean of last 50 iters) ----
        CFILE="postProcessing/forceCoeffs1/0/coefficient.dat"
        # DURABILITY: archive the raw coefficient file so a CSV wipe never loses data
        mkdir -p "$DB/aero_raw"
        [ -f "$CFILE" ] && cp "$CFILE" "$DB/aero_raw/${WING}_a${ALPHA}.dat"
        if [ -f "$CFILE" ]; then
            read CD CL CMP CMR CMY <<< $(tail -50 "$CFILE" | grep -v "^#" | \
              awk '{d+=$2;l+=$5;p+=$8;r+=$9;y+=$10;n++} END{printf "%.6f %.6f %.6f %.6f %.6f",d/n,l/n,p/n,r/n,y/n}')
            ST="ok"; NT=""
            # validity gate: C_D must be positive and O(0.01-0.3)
            python3 -c "exit(0 if 0 < $CD < 1 else 1)" 2>/dev/null || { ST="check"; NT="CD_range"; }
        else
            CD=nan; CL=nan; CMP=nan; CMR=nan; CMY=nan; ST="fail"; NT="no_output"
        fi
        echo "  [$DONE/$TOTAL] $WING α=$ALPHA  C_D=$CD C_L=$CL  ${DT}s $ST"
        echo "$WING,$ALPHA,$CD,$CL,$CMP,$CMR,$CMY,$ST,$DT,$NT" >> "$DB/aero_results.csv"
        sync
    done
    cd /Users/ianzhang/UAUV/cfd
done
echo "=== AERO DONE $(date) | $DB/aero_results.csv | $(grep -c ^Wing $DB/aero_results.csv) data rows ==="
