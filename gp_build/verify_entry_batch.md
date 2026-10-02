# ENTRY Batch Verification Report

**Date:** 2026-08-03
**Script:** `/Users/ianzhang/UAUV/cfd/batch_entry_fixed.sh`
**Template:** `/Users/ianzhang/UAUV/cfd/entry_template/`
**Status:** Verification only -- no files were modified.

---

## 1. force.dat path handling

**Verdict: CORRECT in the batch script, but stale comments exist elsewhere.**

- Batch line 83: `FF="postProcessing/bodyForces/0/force.dat"` -- **correct.**
- The forces function object is named `bodyForces` (line 18 of `system/forces`).
  OpenFOAM uses the function object name as the subdirectory under `postProcessing/`,
  so the output path IS `postProcessing/bodyForces/0/force.dat`.
- An existing run confirmed this path on disk.

**Stale references (wrong path `postProcessing/forces/`):**
- `system/forces` line 13 comment says `// Writes: postProcessing/forces/0/force.dat`.
  Should say `postProcessing/bodyForces/`. This is just a comment and harmless, but
  confusing for future readers.
- `Allrun` line 62 echoes `postProcessing/forces/0/force.dat`. Same stale path.

**Recommendation:** Update the two stale comments/echoes for consistency. Low priority.

---

## 2. 0.orig to 0 copy (including include/ directory)

**Verdict: FUNCTIONALLY CORRECT, but the include/initialConditions file carries stale template values.**

The batch does (lines 70-72):
```bash
rm -rf 0 processor*
cp -r 0.orig 0
cp 0.orig/include/* 0/include/ 2>/dev/null || mkdir -p 0/include && cp 0.orig/include/* 0/include/
```

- `cp -r 0.orig 0` copies the entire tree, including `include/`. The third line is
  redundant belt-and-suspenders and does no harm.
- Verified in an existing run: `0/include/initialConditions` was present and the
  `0/` directory contained all three fields (U, p_rgh, alpha.water).

**HOWEVER, there is a subtle cleanliness issue:**

The Python substitution scripts (lines 46-56) modify `0.orig/U` and `0.orig/p_rgh`
**in place** before the copy. The hardcoded values are:
- `0.orig/U`: `($U_x 0 $U_z)` replaced with e.g. `(18.117333 0 -67.614808)`
- `0.orig/p_rgh`: `$press` replaced with `0`

But `0.orig/include/initialConditions` is **never modified**. After copy, the
`0/include/initialConditions` file still carries the template defaults:
```
U_x     45.315389;
U_z     -21.130913;
press   0;
```

This is **functionally harmless** because both `0/U` and `0/p_rgh` have been
hardcoded (no `$`-substitution needed). The `#include` in those files still
executes but defines variables that are never referenced. Nonetheless, a future
field file that references `$U_x` from the include would silently pick up wrong
values.

**Template safety:** Verified that `entry_template/0.orig/U` is **not** corrupted
by the batch -- the template still has `uniform ($U_x 0 $U_z)`. The batch modifies
the case copy only (it `cd "$DIR"` before the Python runs).

**Recommendation:** Either (a) skip modifying `0.orig` and instead modify `0/`
after the copy, or (b) also rewrite `0.orig/include/initialConditions` to keep it
consistent. Low priority for correctness, medium for maintainability.

---

## 3. reconstructPar after interFoam

**Verdict: YES, but it may never execute if interFoam exits non-zero.**

- Line 79: `mpirun -np $NP interFoam -parallel > log.interFoam 2>&1`
- Line 80: `reconstructPar > /dev/null 2>&1`

`reconstructPar` runs unconditionally after interFoam -- but `set -e` means that
if interFoam exits with any non-zero code, the batch terminates at line 79 and
`reconstructPar` never runs. See issue 4 below.

**Additional observation:** The batch runs `snappyHexMesh -overwrite` **serially**
(no prior decomposePar), while the `Allrun` script decomposes first, runs sHM in
parallel, then runs `reconstructParMesh`. Both approaches are valid for small 2D
cases; the batch skips `restore0Dir` (which Allrun uses) because it manually
replaces `0/` from `0.orig` after sHM. This is fine.

---

## 4. set -e issues

**Verdict: CRITICAL CONCERN -- a single diverged case kills the entire batch with no record.**

`set -e` at line 5 causes the shell to exit on any non-zero return code. The
impact at each pipeline stage:

| Line | Command | Risk |
|------|---------|------|
| 56 | Python inline (0.orig/U) | Low. `str.replace` always succeeds. |
| 57 | Python inline (0.orig/p_rgh) | Low. |
| 62 | `blockMesh` | **Medium.** If blockMesh fails, batch dies before any check. No database entry. |
| 63 | `surfaceFeatureExtract` | **Medium.** Same as above. |
| 64 | `snappyHexMesh` | **Low.** The grep check at line 63-67 catches mesh failures, and `if` conditions do not trigger `set -e`. |
| 66 | `cd /Users/ianzhang/UAUV/cfd` | Low. Path should exist. |
| 72 | `cp 0.orig/include/* ...` | Low. Belt-and-suspenders; `mkdir -p` is robust. |
| 75 | `setFields \|\| true` | **Low.** `\|\| true` prevents `set -e` from triggering. BUT this means a setFields failure is silently ignored -- the simulation runs with wrong phase initialization. |
| 78 | `decomposePar` | Medium. Failure here is truly fatal, but no DB entry. |
| 79 | `mpirun ... interFoam` | **CRITICAL.** If the solver diverges, crashes, or is killed, the entire batch terminates. The failed case gets NO database entry (not even "diverged"), and **all remaining 74 cases are lost.** |
| 80 | `reconstructPar` | Medium. If this fails (e.g., corrupted data), batch dies AFTER the solve but before DB write. |

**The most severe scenario:** interFoam diverges on case 2/75. Cases 3-75 never
run. The database has only 1 row. The user discovers this after 12+ hours.

**Evidence from the existing run:** The V70_th75_m3 case ran interFoam for
779 seconds (13 min) but was killed before reaching endTime. The CSV database
(entry_results.csv) has only the header row -- no data for any case. This is
consistent with `set -e` killing the batch when interFoam was terminated.

**Recommendation:** At minimum, wrap `mpirun ... interFoam` in `|| true` and
check the exit code manually, writing "diverged" to the database rather than
killing the batch. The CFD guidance in the project design notes explicitly says: "Return NaN
on divergence, never crash."

---

## 5. a_peak extraction logic

**Verdict: CORRECT for the force.dat format.**

The extraction (lines 85-99):
```python
lines=[l for l in open('$FF') if not l.startswith('#') and l.strip()]
fmax=0
for l in lines:
    cols=l.split()
    if len(cols)>=4:
        fx=float(cols[1]); fz=float(cols[3])
        fm=math.sqrt(fx*fx+fz*fz)
        if fm>fmax: fmax=fm
print(fmax/$M)
```

The force.dat column layout (verified):
```
# Time      total_x    total_y    total_z    pressure_x  ...  viscous_z
cols[0]     cols[1]    cols[2]    cols[3]    cols[4]          cols[9]
```

- Uses `total_x` (cols[1]) and `total_z` (cols[3]) -- correct for the total
  force columns (not pressure or viscous).
- `len(cols)>=4` ensures at least time + total_(x,y,z) exist.
- The Y-component is ignored. This is acceptable for a 2D case where total_y
  is negligible (verified: -0.87 N vs -6.96e6 N total_z).
- `$FF` and `$M` are expanded by bash (double-quoted `-c "..."`) before Python
  executes. Safe for simple paths and integer masses.
- If force.dat exists but has no data rows (header only), prints "nan". Correct.
- If force.dat does not exist, the whole block is skipped and `a_peak="nan"`.
  Correct.

**Minor concern:** `a_g` computation at line 100:
```bash
a_g=$(python3 -c "print($a_peak/9.81)" 2>/dev/null || echo "nan")
```
If `a_peak="nan"`, the Python `print(nan/9.81)` evaluates to `nan` (NaN is a
valid float), so `|| echo "nan"` never triggers. This works. But if a_peak is
not a valid Python expression (unlikely with the hardcoded path), the fallback
`echo "nan"` catches it. Acceptable.

**Output convention:** `a_peak` is in m/s^2, `a_g` is in g (divided by 9.81).

---

## 6. endTime and peak-capture adequacy

**Verdict: PROBABLY SUFFICIENT for the fast/steep cases, but the comment is wrong by 10x.**

The controlDict has:
```
endTime         0.005;          // 50 ms — sufficient to capture a_peak transient
```

**The value `0.005` = 5 ms, not 50 ms.** Either the value or the comment is wrong.

**Physical reasoning:**
- Body diameter D = 0.10 m, nose length L_n = 0.15 m (Myring profile).
- At V=70 m/s, th=-75 (steepest): effective vertical speed ~67.6 m/s.
  Nose entry time ~ L_n/V = 2.1 ms. Peak force expected within 2-3 ms.
- At V=30 m/s, th=-15 (shallowest): effective vertical speed ~7.8 m/s.
  Nose entry time ~ 19 ms. Peak force could occur later.

**Evidence from the existing run** (V=70, th=-75, m=3, killed at 3.97 ms):
The total_z force was monotonically DECREASING from the earliest logged time
to the last:
```
~6.5e4 N (F_total_x), ~-7.0e6 N (F_total_z) at early times
~-6.8e2 N (F_total_x), ~-1.6e4 N (F_total_z) at 3.97 ms
```
This means the peak WAS captured before 3.97 ms. For this case, 5 ms is adequate.

**Concern for shallow-angle cases:** At V=30 m/s, th=-15, the water approaches
the body at only 7.8 m/s vertically. The impact is far more gradual. The peak
force could occur substantially later than 5 ms. Additionally, the simulation
took 779 s (13 min) to reach only 3.97 ms for one case -- and the runtime scales
with physical time, so reaching 5 ms would take ~16 min per case.

**Additional concern:** The simulation that ran was killed before reaching
endTime 0.005 (last timestep = 3.97 ms), and interFoam was still taking tiny
timesteps (deltaT ~ 1e-6 s). If reaching the full 5 ms requires ~5000+ more
timesteps, runtime per case could be 20+ minutes.

**Recommendation:**
1. Fix the comment to say "5 ms" or change endTime to 0.05 (50 ms) depending
   on which is intended.
2. For the shallow-angle cases, consider extending endTime or verifying with a
   pilot V=30/th=-15 run that the peak is captured within 5 ms.
3. Consider that 75 cases at ~15-20 min each = 19-25 hours total runtime.

---

## 7. Forces function object: rho rhoInf vs rho rho

**Verdict: ACCEPTABLE for water-entry impact forces, but `rho rho;` would be technically more correct.**

The forces dict (`system/forces`) at line 39-40:
```
rho             rhoInf;
rhoInf          1000;
```

The user's instruction references OpenFOAM interFoam documentation: the forces
function object for a two-phase solver should use `rho rho;` for phase-aware
density.

**Analysis:**

The function object type is `forces` (not `forceCoeffs`). For raw force
computation, the force is calculated as:
```
F = sum(p * n * dA) + sum(tau * n * dA)
```
where `p` is the static pressure and `tau` is the viscous stress tensor. Neither
term directly requires density in the integration.

In interFoam, the solver computes `p_rgh` (p - rho*g*h). The forces function
object reconstructs the static pressure as `p = p_rgh + rho*g*h`. The `rho`
here should be the local mixture density (alpha1*rho1 + alpha2*rho2).

- With `rho rhoInf; rhoInf 1000;`: The function uses rho=1000 for ALL cells,
  including air-phase cells. The pressure reconstruction in air cells would be
  wrong (p_rgh + 1000*g*h instead of p_rgh + 1.2*g*h).
- With `rho rho;`: The function object reads the phase-aware density from the
  VOF model (alpha.water*1000 + alpha.air*1.2), giving correct pressure
  reconstruction in both phases.

**Practical impact:** During water-entry impact, the body surface is
overwhelmingly in contact with water (not air). The air-phase contribution to
total force is negligible (air density is ~1/800 of water). Therefore, using
`rhoInf 1000` introduces negligible error for the a_peak metric.

**However**, the forces dict's own comment (lines 36-38) claims "For raw forces,
rho is unused -- the function reads rho from the variable-density VOF field
automatically." This is **not accurate** when `rho rhoInf;` is explicitly set.
Setting `rho rhoInf;` overrides the automatic phase-density lookup.

**Recommendation:** Change to `rho rho;` to be technically correct and consistent
with the interFoam documentation. Remove or correct the misleading comment.
The practical difference for a_peak will be negligible, but it eliminates a
potential source of confusion and ensures correctness for any future use of
force coefficients.

---

## Summary of findings

| # | Item | Status | Severity |
|---|------|--------|----------|
| 1 | force.dat path | Correct in batch; stale comments in forces dict and Allrun | Low |
| 2 | 0.orig-to-0 copy | Functionally correct; stale values in include/initialConditions | Low |
| 3 | reconstructPar order | Yes, runs after interFoam | OK |
| 4 | set -e issues | **One diverged case kills the entire batch silently** | **Critical** |
| 5 | a_peak extraction | Correct for force.dat format | OK |
| 6 | endTime adequacy | 5 ms (not 50 ms); probably OK for steep cases, marginal for shallow | Medium |
| 7 | rho rhoInf vs rho rho | Acceptable for impact but technically imprecise | Low |

**The single highest-priority fix is issue 4:** the `set -e` behavior means a
single diverged `interFoam` case silently kills the entire batch with no
database record. This contradicts the the project design notes guidance: "Return NaN on
divergence, never crash. Persist every evaluation to a CSV keyed by the design
vector so restarts never re-run a case."
