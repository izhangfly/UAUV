#!/bin/bash
# ============================================================================
# HYDRO campaign — simpleFoam k-ω SST, WATER. Reuses AERO meshes (same geometry).
#   Phase 1: all 10 wings × 10 α at V_w=5 m/s          → C_D0,w(Λ), k_w(Λ), C_Lα,w(Λ)
#   Phase 2: Wing90 & Wing0, V_w={2,5,10,15,20} × 6 α   → Re-dependence of polar
#   Phase 3: Wing0 & Wing10, fine α (-8..8) at 5 m/s     → stowed trim C_L,uw(α)
# Output → database/hydro_results.csv
# RUN INSIDE openfoam shell:  source batch_hydro.sh 2>&1 | tee database/hydro_batch.log
# ============================================================================
# set -e intentionally OFF

TEMPLATE=/Users/ianzhang/UAUV/cfd/hydro_template
AERO_TEMPLATE=/Users/ianzhang/UAUV/cfd/aero_template
AERO_CASES=/Users/ianzhang/UAUV/cfd/cases/aero
CASES=/Users/ianzhang/UAUV/cfd/cases/hydro
DB=/Users/ianzhang/UAUV/cfd/database
STL=/Users/ianzhang/UAUV/stl
DECOMP=decomposeParDict.6
NP=6

# ---- HYDRO fluid properties (WATER) ----
RHO=1000           # kg/m3   (forceCoeffs rhoInf — from hydro template)
NU=1.0e-6          # m2/s    (kinematic viscosity of water; matches transportProperties)
TI=0.02            # freestream turbulence intensity
MTR=10             # target inlet μt/μ

WINGS=(Wing0 Wing10 Wing20 Wing30 Wing40 Wing50 Wing60 Wing70 Wing80 Wing90)
ALPHAS=(-4 -2 0 2 4 6 8 10 12 14)
VW_SWEEP=(2 5 10 15 20)

mkdir -p "$DB" "$CASES"
# Append-safe: keep existing CSV so a re-run RESUMES instead of wiping progress
[ -f "$DB/hydro_results.csv" ] || \
  echo "wing,alpha,V_w,C_D,C_L,CmPitch,CmRoll,CmYaw,status,wall_s,notes" > "$DB/hydro_results.csv"

# ---------------------------------------------------------------------------
# run_point WING V_w ALPHA NOTE  — sets up + runs one operating point in $PWD (the case)
# ---------------------------------------------------------------------------
run_point() {
    local WING=$1 VW=$2 ALPHA=$3 NOTE=$4
    # RESUME: skip if this (wing,alpha,V_w) already completed ok
    if grep -q "^$WING,$ALPHA,$VW,.*,ok," "$DB/hydro_results.csv" 2>/dev/null; then
        echo "  $WING α=$ALPHA Vw=$VW  (done, skip)"; return
    fi
    local T0=$(date +%s)

    read Vx Vz DX DZ LX LZ K OM <<< $(python3 -c "
import math
a=math.radians($ALPHA); c=math.cos(a); s=math.sin(a)
U=$VW; nu=$NU; I=$TI; mtr=$MTR
Vx=-U*c; Vz=U*s
DX=-c; DZ=s
LX=s;  LZ=c
k=1.5*(I*U)**2
om=k/(nu*mtr)
print(Vx,Vz,DX,DZ,LX,LZ,k,om)
")

    {
      echo "flowVelocity ($Vx 0 $Vz);"
      echo "pressure 0;"
      echo "turbulentKE $K;"
      echo "turbulentOmega $OM;"
    } > 0.orig/include/initialConditions

    cp "$TEMPLATE/system/forceCoeffs" system/forceCoeffs
    python3 -c "
import re
t=open('system/forceCoeffs').read()
t=re.sub(r'dragDir\s+\([^)]*\);', 'dragDir         ($DX 0 $DZ);', t)
t=re.sub(r'liftDir\s+\([^)]*\);', 'liftDir         ($LX 0 $LZ);', t)
t=re.sub(r'magUInf\s+\S+;',       'magUInf         $VW;', t)
open('system/forceCoeffs','w').write(t)
"

    rm -rf 0 processor* postProcessing; cp -r 0.orig 0
    decomposePar -decomposeParDict "system/$DECOMP" > /dev/null 2>&1
    mpirun -np $NP simpleFoam -parallel > /dev/null 2>&1
    reconstructPar > /dev/null 2>&1
    local T1=$(date +%s); local DT=$((T1-T0))

    local CFILE="postProcessing/forceCoeffs1/0/coefficient.dat"
    # DURABILITY: archive raw coefficients so a CSV wipe never loses data
    mkdir -p "$DB/hydro_raw"
    [ -f "$CFILE" ] && cp "$CFILE" "$DB/hydro_raw/${WING}_a${ALPHA}_Vw${VW}.dat"
    local CD CL CMP CMR CMY ST
    if [ -f "$CFILE" ]; then
        read CD CL CMP CMR CMY <<< $(tail -50 "$CFILE" | grep -v "^#" | \
          awk '{d+=$2;l+=$5;p+=$8;r+=$9;y+=$10;n++} END{printf "%.6f %.6f %.6f %.6f %.6f",d/n,l/n,p/n,r/n,y/n}')
        ST="ok"
        python3 -c "exit(0 if 0 < $CD < 2 else 1)" 2>/dev/null || ST="check"
    else
        CD=nan; CL=nan; CMP=nan; CMR=nan; CMY=nan; ST="fail"
    fi
    echo "  $WING α=$ALPHA Vw=$VW  C_D=$CD C_L=$CL  ${DT}s $ST"
    echo "$WING,$ALPHA,$VW,$CD,$CL,$CMP,$CMR,$CMY,$ST,$DT,$NOTE" >> "$DB/hydro_results.csv"
    sync
}

# ---------------------------------------------------------------------------
# prepare_case WING  — clone AERO mesh, install WATER props + fixed hydro U
# ---------------------------------------------------------------------------
prepare_case() {
    local WING=$1
    local CASE="$CASES/$WING" AERO="$AERO_CASES/$WING"
    if [ ! -d "$CASE/constant/polyMesh" ]; then
        if [ -d "$AERO/constant/polyMesh" ]; then
            # Fast path: reuse AERO mesh if it already exists
            rm -rf "$CASE"; mkdir -p "$CASE"
            cp -r "$AERO/constant" "$AERO/system" "$AERO/0.orig" "$CASE/"
        else
            # Independent path: build our own mesh (no dependence on AERO timing)
            echo "  building own mesh for $WING (AERO mesh not present)"
            rm -rf "$CASE"; cp -r "$AERO_TEMPLATE" "$CASE"
            mkdir -p "$CASE/constant/triSurface"
            for s in NBody VFin HFin Pivot_Actuator_cylinder; do cp "$STL/$s.stl" "$CASE/constant/triSurface/"; done
            cp "$STL/${WING}.stl" "$CASE/constant/triSurface/wing.stl"
            ( cd "$CASE"; cp -r 0.orig 0
              blockMesh            > log.blockMesh 2>&1
              surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1
              snappyHexMesh -overwrite > log.snappyHexMesh 2>&1 )
            if ! grep -q "Finished meshing without any errors" "$CASE/log.snappyHexMesh" 2>/dev/null; then
                echo "  !! MESH FAIL for $WING — see $CASE/log.snappyHexMesh"; return 1
            fi
        fi
    fi
    # Always install water properties + fixed inlet U (idempotent)
    cp "$TEMPLATE/constant/transportProperties" "$CASE/constant/"
    cp "$TEMPLATE/system/forceCoeffs"            "$CASE/system/"
    cp "$TEMPLATE/0.orig/U"                      "$CASE/0.orig/"
    return 0
}

echo "============ PHASE 1: α sweep, all 10 wings, V_w=5 m/s ============"
for WING in "${WINGS[@]}"; do
    echo "=== $(date)  WING=$WING ==="
    prepare_case "$WING" || continue
    cd "$CASES/$WING"
    for ALPHA in "${ALPHAS[@]}"; do run_point "$WING" 5 "$ALPHA" ""; done
    cd /Users/ianzhang/UAUV/cfd
done

echo "============ PHASE 2: V_w sweep, Wing90 (deployed) & Wing0 (stowed) ============"
for WING in Wing90 Wing0; do
    echo "=== $(date)  V_w sweep WING=$WING ==="
    prepare_case "$WING" || continue
    cd "$CASES/$WING"
    for VW in "${VW_SWEEP[@]}"; do
        for ALPHA in -2 0 2 4 6 8; do run_point "$WING" "$VW" "$ALPHA" "vw_sweep"; done
    done
    cd /Users/ianzhang/UAUV/cfd
done

echo "============ PHASE 3: stowed trim, Wing0 & Wing10, fine α, V_w=5 ============"
for WING in Wing0 Wing10; do
    echo "=== $(date)  trim WING=$WING ==="
    prepare_case "$WING" || continue
    cd "$CASES/$WING"
    for ALPHA in $(seq -8 1 8); do run_point "$WING" 5 "$ALPHA" "trim_block"; done
    cd /Users/ianzhang/UAUV/cfd
done

echo "=== HYDRO DONE $(date) | $DB/hydro_results.csv | $(grep -c ^Wing $DB/hydro_results.csv) data rows ==="
