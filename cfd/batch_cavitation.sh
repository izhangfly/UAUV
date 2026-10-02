#!/bin/bash
# ============================================================================
# CAVITATION check — closes the HYDRO gap: -C_p,min(C_L) vs cavitation number σ.
#   Extracts the suction peak (min kinematic pressure) on the wing surface,
#   converts to -C_p,min, and tests against σ(h) for depths 0/2/5/10 m.
#   Cavitation inception when  -C_p,min > σ.
# Configs: Wing0 (stowed = operational underwater) + Wing90 (deployed, strong suction).
# RUN INSIDE openfoam shell:  source batch_cavitation.sh 2>&1 | tee database/cav_batch.log
# ============================================================================
TEMPLATE=/Users/ianzhang/UAUV/cfd/hydro_template
CASES=/Users/ianzhang/UAUV/cfd/cases/hydro
DB=/Users/ianzhang/UAUV/cfd/database
DECOMP=decomposeParDict.6; NP=6
NU=1.0e-6; RHO=1000.0; TI=0.02; MTR=10
PATM=101325.0; PV=2340.0; G=9.81       # Pa, vapour pressure @20C, gravity

WINGS=(Wing0 Wing90)
VW=(5 10 15 20)
ALPHAS=(0 2 4 6 8)

mkdir -p "$DB"
echo "wing,alpha,V_w,p_min,Cp_min,negCp_min,sigma_h0,sigma_h2,sigma_h5,sigma_h10,cav_h0,status" \
  > "$DB/cavitation_results.csv"

# cavitation probe: min kinematic pressure over the wing patch
write_probe() {
cat > system/cavProbe <<'EOF'
cavProbe
{
    type            surfaceFieldValue;
    libs            (fieldFunctionObjects);
    writeControl    onEnd;
    writeFields     false;
    regionType      patch;
    name            wing;
    operation       min;
    fields          (p);
}
EOF
}

for WING in "${WINGS[@]}"; do
    CASE="$CASES/$WING"
    [ -d "$CASE/constant/polyMesh" ] || { echo "  no mesh for $WING — run HYDRO first"; continue; }
    cp "$TEMPLATE/constant/transportProperties" "$CASE/constant/"
    cd "$CASE"
    write_probe
    # register cavProbe alongside forceCoeffs in controlDict (once)
    if ! grep -q 'cavProbe' system/controlDict; then
        cp system/controlDict system/controlDict.cavbak
        python3 -c "
t=open('system/controlDict').read()
t=t.replace('#include \"forceCoeffs\"','#include \"forceCoeffs\"\n    #include \"cavProbe\"')
open('system/controlDict','w').write(t)"
    fi

    for V in "${VW[@]}"; do
      for A in "${ALPHAS[@]}"; do
        read Vx Vz K OM <<< $(python3 -c "
import math
a=math.radians($A); U=$V; nu=$NU; I=$TI; mtr=$MTR
print(-U*math.cos(a), U*math.sin(a), 1.5*(I*U)**2, 1.5*(I*U)**2/(nu*mtr))")
        printf 'flowVelocity (%s 0 %s);\npressure 0;\nturbulentKE %s;\nturbulentOmega %s;\n' \
          "$Vx" "$Vz" "$K" "$OM" > 0.orig/include/initialConditions

        rm -rf 0 processor* postProcessing; cp -r 0.orig 0
        decomposePar -decomposeParDict "system/$DECOMP" >/dev/null 2>&1
        mpirun -np $NP simpleFoam -parallel >/dev/null 2>&1
        reconstructPar >/dev/null 2>&1

        PF=$(find postProcessing/cavProbe -name 'surfaceFieldValue.dat' 2>/dev/null | head -1)
        PMIN=$(tail -1 "$PF" 2>/dev/null | grep -v '^#' | awk '{print $NF}')
        [ -z "$PMIN" ] && PMIN=nan

        read CP NEG S0 S2 S5 S10 CAV <<< $(python3 -c "
V=$V; rho=$RHO; patm=$PATM; pv=$PV; g=$G
try: pmin=float('$PMIN')
except: pmin=float('nan')
q=0.5*V*V                       # kinematic dyn. pressure (OpenFOAM p is p/rho)
Cp=pmin/q; neg=-Cp
sig=lambda h:(patm/rho + g*h - pv/rho)/q
s=[sig(h) for h in (0,2,5,10)]
cav='YES' if neg>s[0] else 'no'
print(f'{Cp:.4f} {neg:.4f} {s[0]:.3f} {s[1]:.3f} {s[2]:.3f} {s[3]:.3f} {cav}')")

        echo "  $WING α=$A Vw=$V  -Cp,min=$NEG   σ(0m)=$S0   cavitates@surface=$CAV"
        echo "$WING,$A,$V,$PMIN,$CP,$NEG,$S0,$S2,$S5,$S10,$CAV,ok" >> "$DB/cavitation_results.csv"
        sync
      done
    done
    # restore original controlDict
    [ -f system/controlDict.cavbak ] && mv system/controlDict.cavbak system/controlDict
    rm -f system/cavProbe
    cd /Users/ianzhang/UAUV/cfd
done
echo "=== CAVITATION DONE $(date) | $DB/cavitation_results.csv ==="
echo "    Cavitation-free envelope IF no row shows cav_h0=YES at V_w=20."
