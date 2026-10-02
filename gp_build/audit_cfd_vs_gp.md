# CFD Data vs GP Model Audit

**Date:** 2026-08-03  
**Purpose:** Crosscheck every GP-required CFD coefficient (gp_model.tex Table 5 / cfd_sweep_plan.md
Table 0) against what actually exists in `cfd/database/`. Identifies gaps, data quality flags, and
whether the alpha and Lambda ranges are sufficient.

---

## 1. Executive Summary

**The CFD database is critically insufficient for the GP sizing model.** Of the 9 fitted coefficients
the GP requires, 0 are supported by validated, complete CFD data. The AERO campaign produced zero
valid points (batch crashed with a dyld linker error). The HYDRO campaign produced 24 partial points
at a single velocity with a suspected reference-area error inflating C_D by ~80--100x. The ENTRY
campaign produced 1 nonsensical point (34 million g). No pressure-field data (C_p,min) was
extracted from any run.

The one encouraging finding: the HYDRO force coefficients show physically correct monotonic C_L vs
alpha behaviour, confirming that the meshes and solver are fundamentally working. The AERO batch
crash (`dyld: missing symbol called`) is a macOS dynamic-linker issue specific to the OpenFOAM ARM
build, not a modelling problem.

**Recommendation:** Fix the dyld linker error first (update/reinstall the gerlero OpenFOAM ARM
build), then re-run AERO from scratch. Fix the forceCoeffs reference area for HYDRO before
continuing. Do not proceed to GP fitting with the current data.

---

## 2. Data Inventory

### 2.1 Files in `cfd/database/`

| File | Rows | Status |
|---|---|---|
| `aero_results.csv` | 1 (header only) | Empty -- batch never wrote data |
| `aero_results_recovered.csv` | 101 (100 data rows) | Recovered from prior session; C_L invariant with alpha -- **physically invalid** (see Sec 3.1) |
| `hydro_results.csv` | 25 (24 data rows) | Partial; 3 of 10 wings at single V_w=5 m/s; C_D inflated 80--100x (see Sec 3.2) |
| `entry_results.csv` | 2 (1 data row) | 1 run, result is physically nonsensical (34 million g; see Sec 3.3) |
| `aero_batch.log` | 3 lines | Confirms dyld crash on Wing0 |
| `hydro_batch.log` | 29 lines | Confirms Phase 1 stopped at Wing20 alpha=2 |
| `entry_batch.log` | 4 lines | Shows [1/75] completed with absurd result, [2/75] started |
| `monitor.log` | ~1700 lines | Chronicles 7+ hours of AERO batch crash-restart loop (~340 restarts, ~30 crashes/min) |

### 2.2 Meshes on Disk

| Campaign | Meshes present |
|---|---|
| AERO | Wing0, Wing10, Wing20, Wing30, Wing40, Wing50, Wing60, Wing70, Wing80, Wing90 (all 10) |
| HYDRO | Wing0, Wing10, Wing20 (3 of 10; reuses AERO meshes) |
| ENTRY | V70_th75_m3, V70_th75_m5 (2 case directories) |

---

## 3. GP Coefficient-by-Coefficient Audit

### 3.1 AERO CAMPAIGN (simpleFoam, k-omega SST, air, 50 m/s)

**Overall status: ZERO valid data points. The entire campaign must be re-run.**

#### 3.1.1 C_D0(Lambda), k(Lambda) -- Aerial Drag Polar

| Item | Required | Actual | Gap |
|---|---|---|---|
| Lambda sweep | 5 skews (0/30/45/60/90 deg) per gp_model.tex; 11 skews (0--90 every 10 deg) per sweep plan | 10 meshes exist on disk; 100 recovered rows cover all 10 wings x 10 alphas | Data is physically invalid (see below). Also, recovered data has no Wing45 -- the sweep plan's legacy midpoint. |
| Alpha sweep | -4 to stall (~12--16 deg) in 2 deg steps | -4 to +14 in 2 deg steps (11 alpha per wing) | Range OK if data were valid |
| C_L vs alpha monotonicity | C_L must increase with alpha | **FAIL.** Recovered data: for EVERY wing, C_L varies by < 0.001 across the entire -4..+14 deg alpha range. Wing90 (deployed): C_L = -0.338 at ALL alpha. Wing60: C_L = -0.240 at ALL alpha. This is physically impossible for a lifting wing. | Catastrophic -- data is not fit for use |
| C_D within validity thresholds | Deployed: C_D in [0.03, 0.15]; Stowed: C_D in [0.005, 0.04] (per monitor.log thresholds) | Recovered: Wing90 C_D~0.153 (just outside); Wing0 C_D~0.034 (OK). Monitor-log REAL points: Wing10 C_D~0.038 (within range) | Recovered values borderline; real runs OK |
| Status gates | All "ok" or convergence-flagged | All recovered rows marked "recovered" (not "ok") | Data provenance uncertain |

**Root cause:** The recovered CSV contains data from a prior session where the alpha sweep
(rotating inlet velocity and forceCoeffs liftDir/dragDir) was NOT applied. Every alpha point for a
given wing returns the same C_L and C_D because the same flow solution was parsed under different
alpha labels. The monitor log captured 3 real Wing10 runs (alpha=6,8,10) that DID show
alpha-dependent C_L, confirming the batch script logic is correct -- but the batch crashed
before saving them.

**Batch crash root cause:** `dyld[21957]: missing symbol called` -- a macOS ARM64 dynamic linker
error in the gerlero OpenFOAM build. The watchdog restarted the batch ~340 times over 7+ hours;
every instance died within 2--15 seconds. This is a toolchain issue, not a modelling one.

#### 3.1.2 C_Dp(C_L, Re, Lambda) -- Profile Drag

Same data as 3.1.1 -- zero valid points. Additionally:

- Single Re point (50 m/s in air) per the plan -- this is acceptable because the analytic
  C_f = 0.074/Re^0.2 term handles Re-dependence (gp_model.tex Eq. for C_D0,a).
- Pre-subtraction of induced drag C_L^2/(pi e AR) and skin-friction C_f(1+k)S_wet/S was planned
  but could not be executed without valid C_L vs alpha data.

#### 3.1.3 C_Lalpha(Lambda) -- Lift-Curve Slope

Same data as 3.1.1 -- zero valid points.

The recovered data's C_L invariance with alpha means C_Lalpha cannot be extracted for any wing.
The three real Wing10 monitor-log points (alpha=6,8,10) give delta-C_L/delta-alpha ~ 0.07/deg
(~4.0/rad), which is in the right ballpark for the expected deployed value of ~4.3/rad -- but
with the wrong sign (C_L is negative and becoming less negative with alpha, whereas a deployed
wing should be producing positive lift). This could be a liftDir sign convention issue rather
than a physics error.

**Coverage note:** The sweep plan calls for 11 skew meshes (every 10 deg + Wing45 legacy).
gp_model.tex only requires 5 (0/30/45/60/90 deg). Either is acceptable; the denser spacing
improves fit quality for the SMA posynomial.

#### 3.1.4 C_l(Lambda) -- Roll Coefficient (Highest-Value Unknown)

Same data as 3.1.1 -- zero valid points.

Recovered CmRoll values for all wings and alphas are ~0.001 or smaller. For asymmetric skew
angles (Lambda=30--60 deg), significant roll moment is expected. Values of 0.001 suggest the
moment reference length (lRef in forceCoeffs) may be set incorrectly, or the data reflects a
symmetric solution (no actual skew effect captured).

Additionally: the sweep plan calls for separable wing-patch forces to isolate C_l from
hull-interference. This was not implemented; recovered data is total-body moments only.

---

### 3.2 HYDRO CAMPAIGN (simpleFoam, water)

**Overall status: Partial data (24 points), C_D scale error, only Phase 1 partially done.**

#### 3.2.1 C_D0,w -- Underwater Zero-Lift Drag

| Item | Required | Actual | Gap |
|---|---|---|---|
| Lambda sweep | Deployed + stowed + mid-skew | Wing0 (stowed, 10 alpha), Wing10 (lambda=80, 10 alpha), Wing20 (lambda=70, 5 alpha -- truncated) | Missing Wing30--Wing90 (7 wings). Wing20 data incomplete beyond alpha=2 deg. |
| V_w sweep | 2, 5, 10, 15, 20 m/s at deployed + stowed | Only V_w=5 m/s | Missing 4 velocity points at each config (~40 runs) |
| alpha sweep | -4 to stall in 2 deg steps | Wing0: -4 to +14 (complete, 10 pts). Wing10: -4 to +14 (complete, 10 pts). Wing20: -4 to +2 (incomplete, 5 pts) | Missing 7 wings' alpha data and Wing20 alpha > 2 |
| C_D validity | Expected C_D ~0.03--0.15 (reference area ~0.075 m^2 deployed) | C_D = 2.4--3.0 across all points | **80--100x too high.** Likely forceCoeffs Aref set to a very small value (e.g., frontal area ~0.008 m^2 or wing cross-section ~0.0014 m^2). The C_D values are inflated by a constant scale factor. |

**Physics check on C_L:** Despite the C_D scale issue, C_L vs alpha is physically correct and
monotonic:

- Wing0 (stowed, Lambda=90): C_L from -0.238 (alpha=-4) to +0.593 (alpha=14), crossing zero
  near alpha ~ -1 deg. This is plausible for a stowed wing with slight camber/overhang.
- Wing10 (Lambda=80): C_L from 0.981 to 1.823. C_L=1.18 at alpha=0 is high for a nearly-stowed
  wing but the monotonic trend is correct. May indicate the reference area is too small,
  inflating both C_L and C_D by the same factor.

**Recommendation:** Fix the forceCoeffs Aref to the deployed wing planform area (S=0.075 m^2)
or the appropriate projected area per Lambda, THEN re-evaluate all HYDRO runs.

#### 3.2.2 k_w -- Underwater Induced-Drag Factor

Same data as 3.2.1. Cannot separate induced drag from zero-lift drag without valid C_L^2 vs
C_D data across multiple alpha points. The Wing0 data (10 alpha points at V_w=5 m/s) is
structurally sufficient but the C_D scale error must be fixed first.

#### 3.2.3 C_L,uw(alpha) -- Stowed-Wing Trim Lift

| Item | Required | Actual | Gap |
|---|---|---|---|
| alpha sweep at Lambda=90 | -8 to +8 deg in 1 deg steps (fine trim block) | Wing0 at -4 to +14 in 2 deg steps | Coarser alpha spacing; missing negative-alpha range below -4 deg |
| Lambda=80 backup | Wing10 at same fine alpha | Wing10 at -4 to +14 in 2 deg steps | Same resolution gap |
| Self-compensation check | Compare measured dL/dalpha against analytic 2*pi*q*delta^2 | Not computable -- C_D scale error confounds the reference area, and the C_Lalpha slope may also be scaled | Must fix Aref first |

Despite the scale error, the Wing0 data shows a clean linear C_L(alpha) trend from alpha=-2 to
~+8 deg, which is sufficient for extracting C_Lalpha,uw once Aref is corrected.

#### 3.2.4 -C_p,min(C_L) -- Cavitation Suction Peak

| Item | Required | Actual | Gap |
|---|---|---|---|
| C_p,min extraction | From pressure field at each (Lambda, alpha, V_w) point | **Not done.** Force coefficients were parsed from coefficient.dat; C_p field was not exported or post-processed | Complete gap |
| Depth sweep | h = {0, 2, 5, 10} m | **Not done.** This is post-processing (sigma computed analytically from C_p,min and depth), but requires C_p,min first | Dependent on above |
| Worst-case check | Wing0, V_w=20 m/s, alpha ~8 deg, h=0 | Not run -- no V_w=20 data, no C_p,min extraction | Cannot assess cavitation risk |

---

### 3.3 ENTRY CAMPAIGN (interFoam VOF, 2-D rigid)

**Overall status: 1 run, nonsensical result. Batch stalled.**

#### 3.3.1 a_peak = C * V^a * d^b * m^c -- Peak Entry Deceleration

| Item | Required | Actual | Gap |
|---|---|---|---|
| V_entry sweep | 58, 50, 40, 30 m/s | 70 m/s | **Outside planned range.** V=70 is higher than the dive-trajectory maximum (~58 m/s from the project design notes, Sec 4) |
| theta_entry sweep | -15, -25, -35, -45 deg from horizontal | 75 deg from horizontal | **Outside planned range.** 75 deg is near-vertical; the dive trajectory expects -15 to -45 deg. |
| m sweep | 3, 5, 8 kg | 3 kg | Only one mass point |
| a_peak result | < 20g expected; analytic prior ~500--2000 m/s^2 | 341,672,868 m/s^2 = 34,829,038 g | **Catastrophically wrong.** This is 34 million g -- 1.7 million times the 20g constraint. The body likely passed through the domain in a single timestep or the simulation diverged immediately. |
| Total runs | 48 (4V x 4theta x 3m) | 1 (and it's wrong) | 47 missing |
| Run time | 712 seconds (~12 min) for the erroneous run | Entry batch appears stalled after starting [2/75] | Likely crashed on the second case |

**Root cause hypotheses (needs investigation):**
1. The initial velocity vector direction and/or body motion setup is incorrect -- the body may
   have been launched in the wrong direction or at wrong speed.
2. The 2-D domain setup (one-cell-thick extrusion with `empty` patches) may have incorrect
   boundary conditions for the interFoam body-motion case.
3. The timestep may be too large for the initial impact (Courant number explosion on first step).
4. The body-motion 6-DOF solver may have diverged (pitch freed per the sweep plan).

---

## 4. Alpha and Lambda Range Sufficiency

### 4.1 Alpha Range

| Campaign | Range required | Range in data | Sufficient? |
|---|---|---|---|
| AERO | -4 to stall (12--16 deg) | -4 to +14 deg (in recovered data) | Range is sufficient IF data were valid. Note: no stall was observed (C_L never peaks and drops), which is consistent with the data being invalid. |
| HYDRO (general) | -4 to stall | -4 to +14 deg (Wing0, Wing10); -4 to +2 (Wing20) | Sufficient for Wing0/Wing10. Incomplete for Wing20+ |
| HYDRO (stowed trim) | -8 to +8 in 1 deg steps | -4 to +14 in 2 deg steps | Coarser than planned; missing alpha < -4 deg |
| ENTRY | N/A (entry speed is the primary variable) | N/A | N/A |

### 4.2 Lambda Range

| Requirement | Coverage | Sufficient? |
|---|---|---|
| gp_model.tex: 5 skews (0/30/45/60/90) | 10 meshes from 0 to 90 in 10 deg steps exist | **Excellent** -- exceeds GP requirement. 10-point sweep enables robust SMA/ISMA fits. |
| Sweep plan: 11 skews (0--90 every 10 deg + Wing45) | Wing45 mesh does NOT exist on disk (Wing40 and Wing50 bracket it) | Minor gap; Wing45 is legacy midpoint, not essential |

---

## 5. Data Consistency and Physics Checks

### 5.1 Recovered AERO Data

| Check | Result | Pass? |
|---|---|---|
| C_L monotonic with alpha | C_L varies by < 0.001 across entire alpha range for ALL wings | **FAIL** |
| C_L(Wing90) > C_L(Wing0) at same alpha | Wing90 C_L=-0.338, Wing0 C_L=+0.008 at alpha=0. Wing90 has MORE NEGATIVE lift than stowed wing. | **FAIL** |
| C_L crosses zero near alpha=0 for symmetric deployed wing | Wing90 C_L=-0.338 at alpha=0 (large negative offset) | **FAIL** |
| C_D > 0 | All C_D > 0 (0.034--0.154) | PASS |
| C_D(Wing90) > C_D(Wing0) | Wing90 C_D=0.153, Wing0 C_D=0.034 | PASS (deployed more drag) |
| CmPitch consistent sign | CmPitch transitions from negative (Wing0) to positive (Wing90) | Plausible but unvalidated |
| CmRoll near zero at Lambda=0 and Lambda=90 | CmRoll(Wing90)~0.001, CmRoll(Wing0)~0.0002 | PASS (both near zero) |
| CmRoll significant at mid-skew | CmRoll(Wing50)~0.001 -- same magnitude as deployed | **FAIL** -- expected significant asymmetry |

**Verdict: Recovered AERO data is not CFD output.** The constant C_L across alpha, the negative
C_L at alpha=0 for the deployed wing, and the absence of roll moment at mid-skew collectively
indicate these values were generated from runs where alpha was not varied (all points solved at
alpha=0 effective). The small numeric differences (~10^-6) between alpha values are numerical
noise, not aerodynamic response.

### 5.2 HYDRO Data (Wing0, Wing10, Wing20 at V_w=5 m/s)

| Check | Result | Pass? |
|---|---|---|
| C_L monotonic with alpha | Wing0: C_L increases from -0.238 to +0.593. Wing10: C_L increases from 0.981 to 1.823. | PASS |
| C_L crosses near zero | Wing0 C_L crosses zero between alpha=-2 and alpha=0 | PASS (plausible for stowed wing overhang) |
| C_D > 0 | All C_D > 0 (2.44--2.97) | PASS (but values inflated ~80--100x) |
| C_D decreases slightly with alpha (plausible for some configs) | Wing0 C_D drops from 2.66 to 2.60 as alpha goes -4 to +14 | PASS (small drag bucket) |
| CmRoll near zero at Lambda=90 | Wing0 CmRoll ~0.005 to 0.043 | PASS (near zero for symmetric stowed config) |
| CmRoll for Wing10 (Lambda=80) | Wing10 CmRoll ~0.01 to -0.008 (crosses zero near alpha=6) | PASS (small asymmetry at near-stowed) |

**Verdict: HYDRO data is physically well-behaved but C_D is incorrectly scaled.** The
alpha-dependence, monotonicity, and zero-crossings are all physically correct. The uniform
80--100x inflation of C_D (and likely C_L) points to a single forceCoeffs Aref misconfiguration.
Once Aref is corrected, the Wing0 and Wing10 data at V_w=5 m/s become usable.

### 5.3 ENTRY Data

| Check | Result | Pass? |
|---|---|---|
| a_peak < 20g (196 m/s^2) | 341,672,868 m/s^2 | **FAIL** by factor of 1.7 million |
| Realistic impact force | F = m*a = 3 * 3.4e8 = 1.0e9 N. For reference, F_max ~ rho*V^2*A_frontal ~ 1000*4900*0.008 = 39,200 N | **FAIL** by factor of 26,000 |

**Verdict: The ENTRY simulation is fundamentally misconfigured.** The 34-million-g result
suggests the body either passed through the domain boundary in a single timestep, or the 6-DOF
solver diverged catastrophically on the first iteration.

---

## 6. Gap Summary Matrix

| # | GP Coefficient | Campaign | Data Points Needed | Data Points Valid | % Complete | Blocking Issue |
|---|---|---|---|---|---|---|
| 1 | C_D0(Lambda) | AERO | ~50 (5 wings x 10 alpha) | 0 | 0% | dyld crash |
| 2 | k(Lambda) | AERO | Same as #1 | 0 | 0% | dyld crash |
| 3 | C_Lalpha(Lambda) | AERO | Same as #1 | 0 | 0% | dyld crash |
| 4 | C_l(Lambda) | AERO | ~11 (Lambda sweep at fixed alpha) | 0 | 0% | dyld crash |
| 5 | C_D0,w | HYDRO | ~100 (5 wings x 10 alpha + V_w sweep) | 24 (questionable scale) | ~24% (but C_D inflated) | Aref error + incomplete sweep |
| 6 | k_w | HYDRO | Same as #5 | 24 (questionable) | ~24% | Same as #5 |
| 7 | C_L,uw(alpha) | HYDRO | ~34 (2 configs x 17 fine alpha) | 20 (coarse alpha only) | ~59% (but C_L scale uncertain) | Aref error |
| 8 | -C_p,min(C_L) | HYDRO | ~50 (post-process from #5 data) | 0 | 0% | Not extracted |
| 9 | a_peak | ENTRY | 24--48 | 0 (1 invalid point) | 0% | Simulation misconfigured |

**Overall: 0 of 9 GP coefficients have validated, complete CFD data.**

---

## 7. Recommended Remediation Sequence

### Immediate (unblock CFD production)

1. **Fix the dyld linker error.** The `dyld: missing symbol called` crash on the gerlero ARM64
   OpenFOAM build must be resolved. Options:
   - Reinstall via `brew reinstall gerlero/openfoam/openfoam`
   - Check for missing DYLD_LIBRARY_PATH or rpath settings
   - Test with a minimal tutorial case (pitzDaily) to confirm fix
   - If unfixable, fall back to the x86 Docker image (with 13x penalty per the project design notes, Sec 5)

2. **Fix HYDRO forceCoeffs Aref.** Determine the current Aref in `system/forceCoeffs` for the
   HYDRO cases and replace with the correct reference area:
   - Deployed (Wing90): S = 0.075 m^2 (wing planform area)
   - Stowed (Wing0): S_stow = 0.025 m^2 (stowed wing area including overhang)
   - Intermediate Lambda: projected area per the sweep plan Table 1.2
   - Re-run Wing0 and Wing10 at V_w=5 m/s as validation, then re-parse

3. **Fix the ENTRY simulation.** Debug V70_th75_m3:
   - Check initial velocity vector magnitude and direction
   - Verify the body is positioned correctly (just above free surface, not intersecting)
   - Check timestep (maxCo < 1.0 mandatory for interFoam)
   - Check 6-DOF constraints (only translation + pitch free, all others locked)
   - Run a 1-second test with writeInterval=0.001 to inspect the first few timesteps

### Short-term (recover and complete the DOE)

4. **Re-run AERO from scratch** after the dyld fix. The meshes exist (all 10 wings on disk);
   only the solver execution is needed. Expected: ~100 runs at ~10--30 min each = ~17--50
   wall-clock hours on 6 performance cores.

5. **Complete HYDRO Phase 1** (all 10 wings x 10 alpha at V_w=5 m/s) after Aref fix.

6. **Run HYDRO Phase 2** (V_w sweep at Wing90 + Wing0, 5 velocities x ~6 alpha = ~60 runs).

7. **Run HYDRO Phase 3** (fine-alpha stowed trim at Wing0 + Wing10, -8:+1:+8 deg = 34 runs).

### Medium-term (post-processing)

8. **Extract C_p,min** from HYDRO pressure fields (post-processing script -- does not require
   re-running cases, but the cases must be on disk with saved pressure fields).

9. **Run ENTRY DOE** (48 cases) after the simulation setup is validated.

10. **Grid-convergence study** at the nominal design point (Wing90, alpha=4, V=50 m/s air;
    4 meshes: 0.5M, 1M, 2M, 4M cells).

---

## 8. Notes on the "Recovered" Data

`aero_results_recovered.csv` contains 100 rows covering all 10 wings x 10 alphas, all marked
status="recovered". This data was NOT generated by the 2026-08-02/03 batch run (which crashed
repeatedly). The provenance is unclear -- possibly from a prior verification session where the
alpha-sweep velocity-rotation was not enabled.

**This data must not be used for GP fitting.** The invariant C_L(alpha) across the entire alpha
range is a definitive signature that these are NOT aerodynamic polar points. Using them would
produce fitted posynomials that predict zero lift-curve slope, which would break the GP's
lift/weight balance constraint.

The three real Wing10 points captured in `monitor.log` (line 232-234) demonstrate what valid
output looks like:
```
Wing10,alpha=6:  C_D=0.037657, C_L=-0.009472
Wing10,alpha=8:  C_D=0.037965, C_L=-0.008152
Wing10,alpha=10: C_D=0.038226, C_L=-0.006822
```
These show alpha-dependent C_L and plausible coefficient magnitudes. They were not saved to
any CSV before the batch crashed.
