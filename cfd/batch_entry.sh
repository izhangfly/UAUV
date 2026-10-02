#!/bin/bash
# ===========================================================================
# ENTRY campaign batch runner -- 2-D interFoam water-entry DOE
# ===========================================================================
#
# Sweep variables (from cfd_sweep_plan.md §3):
#   V_entry  = {58, 50, 40, 30}      m/s
#   theta    = {-15, -25, -35, -45}   degrees from horizontal
#   m_body   = {3, 5, 8}             kg
#
# Total: 4 x 4 x 3 = 48 cases.
#
# Output per case:
#   - Force time history: postProcessing/forces/0/force.dat
#   - a_peak = max|F_vector| / m_body  (computed in post-processing)
#   - Results aggregated into results.csv
#
# Restart-safe: skips cases that already have force.dat output.
#
# Usage:
#   ./batch_entry.sh                            # all 48 cases
#   ./batch_entry.sh --dry-run                   # print commands only
#   ./batch_entry.sh --start 12                  # resume from case 12
#   ./batch_entry.sh V=50 theta=-25 m=5          # single case
#   NPROCS=4 ./batch_entry.sh                    # override nProcs
# ===========================================================================

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="${SCRIPT_DIR}/entry_template"
RUNS_DIR="${SCRIPT_DIR}/entry_runs"
RESULTS_FILE="${SCRIPT_DIR}/entry_results.csv"
NPROCS="${NPROCS:-6}"          # MPI ranks (M3 Pro 6P cores)
DRY_RUN=false
START_INDEX=0

# --- Parse command-line arguments ---
V_SINGLE=""
THETA_SINGLE=""
M_SINGLE=""

for arg in "$@"; do
    case "$arg" in
        --dry-run)    DRY_RUN=true ;;
        --start)      START_INDEX="${2:-0}"; shift ;;
        V=*)          V_SINGLE="${arg#V=}" ;;
        theta=*)      THETA_SINGLE="${arg#theta=}" ;;
        m=*)          M_SINGLE="${arg#m=}" ;;
        *)            echo "Unknown arg: $arg"; exit 1 ;;
    esac
    shift 2>/dev/null || true
done

# --- Build case list ---
if [ -n "$V_SINGLE" ] && [ -n "$THETA_SINGLE" ] && [ -n "$M_SINGLE" ]; then
    # Single-case mode
    V_LIST=("$V_SINGLE")
    THETA_LIST=("$THETA_SINGLE")
    M_LIST=("$M_SINGLE")
else
    V_LIST=(58 50 40 30)
    THETA_LIST=(-15 -25 -35 -45)
    M_LIST=(3 5 8)
fi

# --- Check environment ---
if ! command -v openfoam &>/dev/null; then
    echo "ERROR: openfoam not found. Source the OpenFOAM environment first."
    exit 1
fi

if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "ERROR: template directory not found: $TEMPLATE_DIR"
    exit 1
fi

# --- Initialise results CSV ---
if [ "$DRY_RUN" = false ] && [ ! -f "$RESULTS_FILE" ]; then
    echo "case_name,V_entry,theta_deg,m_kg,time_peak_s,Fx_peak_N,Fz_peak_N,Fmag_peak_N,a_peak_ms2,a_peak_g,converged,notes" > "$RESULTS_FILE"
fi

# --- Helper: compute velocity components ---
deg2rad() {
    python3 -c "import math; print(math.radians($1))"
}

velocity_components() {
    # V_entry, theta_deg -> Ux, Uz
    # In body-fixed frame (body stationary, water approaches):
    # theta_deg is negative (descending). Water approaches FROM below-left.
    # Ux = V * cos(theta)   (positive = left-to-right in domain)
    # Uz = V * sin(theta)   (negative = upward in domain, toward body)
    # For theta = -25 deg, V=50: Ux=45.3, Uz=-21.1
    python3 -c "
import math
V = $1
th = math.radians($2)
ux = V * math.cos(th)
uz = V * math.sin(th)
print(f'{ux:.6f} {uz:.6f}')
"
}

# --- Helper: compute peak acceleration from force.dat ---
parse_peak_force() {
    local force_file="$1"
    local mass="$2"
    python3 -c "
import sys
import math

# Read force.dat, skip comment lines, find peak |F|
# Columns: Time Fp_x Fp_y Fp_z Fv_x Fv_y Fv_z Fpo_x Fpo_y Fpo_z

times = []
f_mags = []

with open('$force_file', 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('Time'):
            continue
        parts = line.split()
        if len(parts) < 10:
            continue
        try:
            t  = float(parts[0])
            fx = float(parts[1]) + float(parts[4])  # pressure + viscous
            fy = float(parts[2]) + float(parts[5])
            fz = float(parts[3]) + float(parts[6])
            fmag = math.sqrt(fx*fx + fy*fy + fz*fz)
            times.append(t)
            f_mags.append(fmag)
        except (ValueError, IndexError):
            continue

if not f_mags:
    print('NaN NaN NaN NaN NaN NaN False no_data')
    sys.exit(0)

# Find peak
peak_idx = max(range(len(f_mags)), key=lambda i: f_mags[i])
t_peak   = times[peak_idx]
fmag_peak = f_mags[peak_idx]

# Get individual components at peak
# Re-read to get components at peak time
fx_peak = 0; fz_peak = 0
with open('$force_file', 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('Time'):
            continue
        parts = line.split()
        if len(parts) < 10:
            continue
        try:
            t = float(parts[0])
            if abs(t - t_peak) < 1e-10:
                fx_peak = float(parts[1]) + float(parts[4])
                fz_peak = float(parts[3]) + float(parts[6])
                break
        except (ValueError, IndexError):
            continue

mass = float($mass)
a_peak = fmag_peak / mass
a_peak_g = a_peak / 9.81

print(f'{t_peak:.6f} {fx_peak:.3f} {fz_peak:.3f} {fmag_peak:.3f} {a_peak:.3f} {a_peak_g:.3f}')
" 2>/dev/null || echo "NaN NaN NaN NaN NaN NaN False parse_error"
}

# --- Main loop ---
mkdir -p "$RUNS_DIR"

case_index=0
total_cases=$((${#V_LIST[@]} * ${#THETA_LIST[@]} * ${#M_LIST[@]}))

echo "============================================"
echo " ENTRY campaign batch — 2-D interFoam VOF"
echo " Template: $TEMPLATE_DIR"
echo " Runs dir: $RUNS_DIR"
echo " Results:  $RESULTS_FILE"
echo " nProcs:   $NPROCS"
echo " Total cases: $total_cases"
echo "============================================"
echo ""

for V in "${V_LIST[@]}"; do
for theta in "${THETA_LIST[@]}"; do
for m in "${M_LIST[@]}"; do

    case_index=$((case_index + 1))
    if [ "$case_index" -lt "$START_INDEX" ]; then
        continue
    fi

    # Build case name and directory
    theta_abs="${theta#-}"                    # strip leading minus for dir name
    theta_abs="${theta_abs#-}"
    case_name="V${V}_th${theta_abs}_m${m}"
    case_dir="${RUNS_DIR}/${case_name}"

    echo "--- [$case_index / $total_cases] $case_name ---"

    # Compute velocity components
    read Ux Uz <<< "$(velocity_components $V $theta)"
    echo "    U = (${Ux}, 0, ${Uz}) m/s"

    # Skip if already complete
    force_dat="${case_dir}/postProcessing/forces/0/force.dat"
    if [ -f "$force_dat" ] && [ "$DRY_RUN" = false ]; then
        echo "    [SKIP] force.dat exists"
        # Still write result row in case it was missed before
        read t_peak fx fz fmag a_ms2 a_g <<< "$(parse_peak_force "$force_dat" "$m")"
        echo "${case_name},${V},${theta},${m},${t_peak},${fx},${fz},${fmag},${a_ms2},${a_g},True,restart_skip" >> "$RESULTS_FILE"
        continue
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "    [DRY RUN] Would create $case_dir"
        continue
    fi

    # --- Prepare case ---
    echo "    Preparing case directory..."
    mkdir -p "$case_dir"
    # Copy template excluding generated/cache dirs
    rsync -a --exclude='postProcessing' --exclude='processor*' \
              --exclude='constant/triSurface' \
              --exclude='constant/extendedFeatureEdgeMesh' \
              "${TEMPLATE_DIR}/" "${case_dir}/"

    # Update initialConditions with the correct velocity
    cat > "${case_dir}/0.orig/include/initialConditions" << EOF
// Auto-generated by batch_entry.sh
// Case: $case_name  V=${V} m/s  theta=${theta} deg  m=${m} kg
U_x       ${Ux};
U_z       ${Uz};
press     0;
EOF

    # Note: mass is stored for post-processing; not needed by CFD

    # --- Generate STL and mesh ---
    echo "    Generating STL..."
    cd "$case_dir"
    mkdir -p constant/triSurface
    python3 "${TEMPLATE_DIR}/create_nose_stl.py" constant/triSurface/bodyNose.stl || {
        echo "    [FAIL] STL generation failed"
        echo "${case_name},${V},${theta},${m},NaN,NaN,NaN,NaN,NaN,NaN,False,stl_fail" >> "$RESULTS_FILE"
        cd "$SCRIPT_DIR"
        continue
    }

    echo "    surfaceFeatureExtract..."
    surfaceFeatureExtract 2>&1 | tail -1 || true

    echo "    blockMesh..."
    blockMesh 2>&1 | tail -3 || {
        echo "    [FAIL] blockMesh failed"
        echo "${case_name},${V},${theta},${m},NaN,NaN,NaN,NaN,NaN,NaN,False,blockMesh_fail" >> "$RESULTS_FILE"
        cd "$SCRIPT_DIR"
        continue
    }

    echo "    decomposePar..."
    decomposePar -decomposeParDict "system/decomposeParDict.${NPROCS}" -force 2>&1 | tail -1 || true

    echo "    snappyHexMesh (parallel)..."
    mpirun -np "$NPROCS" snappyHexMesh -overwrite -parallel 2>&1 | tail -10 || {
        echo "    [FAIL] snappyHexMesh failed"
        echo "${case_name},${V},${theta},${m},NaN,NaN,NaN,NaN,NaN,NaN,False,snappy_fail" >> "$RESULTS_FILE"
        cd "$SCRIPT_DIR"
        continue
    }

    echo "    reconstructParMesh..."
    reconstructParMesh -constant 2>&1 | tail -1 || true

    echo "    setFields..."
    setFields 2>&1 | tail -1 || true

    echo "    decomposePar (solve)..."
    decomposePar -decomposeParDict "system/decomposeParDict.${NPROCS}" -force 2>&1 | tail -1 || true

    # Restore 0.orig to processor dirs
    if [ -d "processor0" ]; then
        for pdir in processor*; do
            if [ -d "$pdir" ]; then
                cp -r 0.orig/* "$pdir/0/" 2>/dev/null || true
            fi
        done
    fi

    # --- Run interFoam ---
    echo "    interFoam (${NPROCS} procs)..."
    mpirun -np "$NPROCS" interFoam -parallel 2>&1 | tail -20 || {
        echo "    [WARN] interFoam exited non-zero"
    }

    echo "    reconstructPar..."
    reconstructPar -latestTime 2>&1 | tail -1 || true

    # --- Parse results ---
    cd "$SCRIPT_DIR"
    if [ -f "$force_dat" ]; then
        read t_peak fx fz fmag a_ms2 a_g <<< "$(parse_peak_force "$force_dat" "$m")"
        echo "    t_peak = ${t_peak} s, F_peak = ${fmag} N, a_peak = ${a_ms2} m/s^2 (${a_g} g)"
        echo "${case_name},${V},${theta},${m},${t_peak},${fx},${fz},${fmag},${a_ms2},${a_g},True," >> "$RESULTS_FILE"
    else
        echo "    [FAIL] No force.dat output"
        echo "${case_name},${V},${theta},${m},NaN,NaN,NaN,NaN,NaN,NaN,False,no_output" >> "$RESULTS_FILE"
    fi

    echo ""

done
done
done

echo "============================================"
echo " ENTRY campaign batch complete."
echo " Results: $RESULTS_FILE"
echo "============================================"

# Print summary
if [ -f "$RESULTS_FILE" ] && [ "$DRY_RUN" = false ]; then
    echo ""
    echo "Summary (first 5 rows + tail):"
    head -6 "$RESULTS_FILE"
    echo "..."
    tail -5 "$RESULTS_FILE"
    echo ""
    n_total=$(tail -n +2 "$RESULTS_FILE" | wc -l | tr -d ' ')
    n_conv=$(tail -n +2 "$RESULTS_FILE" | grep ",True," | wc -l | tr -d ' ')
    n_fail=$(tail -n +2 "$RESULTS_FILE" | grep ",False," | wc -l | tr -d ' ')
    echo "Total: $n_total | Converged: $n_conv | Failed: $n_fail"
fi

# ************************************************************************* //
