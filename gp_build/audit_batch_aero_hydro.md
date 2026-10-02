# Full Audit — AERO & HYDRO Batch Processing (2026-08-03)

Audited `batch_aero.sh`, `batch_hydro.sh`, templates, and case state against `gp_model.tex`
CFD requirements. Below: every bug, its effect, and the fix.

## Bugs found

| # | File | Bug | Effect | Fix |
|---|---|---|---|---|
| A1 | batch_aero.sh L41 | `DX = +math.cos(r)` (sloppy global sed corrupted it) | dragDir points WITH flow → **C_D negative** | `DX = -math.cos(r)` |
| A2 | batch_aero + hydro | `LX = -math.sin(r)` | liftDir NOT ⊥ dragDir at α≠0 (cross-contamination sin2α, e.g. 34% at α=10°) → **corrupts C_Lα slope** | `LX = +math.sin(r)` |
| A3 | AERO cases 0.orig/U | inlet hardcoded `uniform (-50 0 0)` (built from old template) | inlet ignores `$flowVelocity` → **α sweep produces identical result every α** | refresh `0.orig/U` from fixed template each wing |
| A4 | both, forceCoeffs sub | `re.sub` runs on already-substituted file each α, doesn't consume trailing `;` | semicolons accumulate `;;;;;;` (cosmetic) + risk of pattern drift | copy fresh `forceCoeffs` from template each α iteration, sub once |
| A5 | both, turbulence | `k=0.24, ω=1.78` fixed (motorBike 20 m/s values) | μt/μ ≈ 9000 (air) / 135000 (water) — **massively over-diffusive**, wrong at every V | compute `k,ω` from U each point, target μt/μ=10, I=2% |
| A6 | HYDRO (earlier) | inlet 50 m/s while magUInf=5 | q wrong by (50/5)²=100× → **C_D inflated 100×** | fixed via A3 (inlet=$internalField) |
| A7 | HYDRO | `rhoInf` comment says "air" but value 1000 | cosmetic only | comment corrected |

## GP-requirement coverage (gp_model.tex §5 CFD table)

| GP coefficient | Campaign | DOE | Batch produces? |
|---|---|---|---|
| C_D0(Λ), k(Λ) — aerial drag polar | AERO | α×Λ | ✅ C_D, C_L per (wing,α) |
| C_Dp(C_L,Re,Λ) | AERO | α×Λ | ✅ same data |
| C_Lα(Λ) — lift slope | AERO | α×Λ | ✅ (needs A2/A3 fix for valid slope) |
| C_l(Λ) — roll authority | AERO | Λ | ✅ CmRoll (col 9). NOTE: total-vehicle roll ≈ wing roll (fins symmetric); wing-only FO is an enhancement |
| C_D0,w, k_w — underwater polar | HYDRO | α×Λ + V_w | ✅ Phase 1 + Phase 2 |
| C_L,uw(α) — stowed trim | HYDRO | α at Λ=90 | ✅ Phase 3 trim block (Wing0/Wing10, fine α) |
| −C_p,min(C_L) — cavitation | HYDRO | α×V_w×h | ⚠️ **GAP**: force coeffs recorded but not min-pressure. Extract via post-pass on saved p field (documented below) |
| a_peak — entry impact | ENTRY | separate | (2-D interFoam, separate track) |

## Sign convention (now consistent, both scripts)

Freestream at AoA α: **U = magU·(−cos α, 0, +sin α)** (flow in −X, tilts +Z for +α = more lift).
- dragDir = U/|U| = **(−cos α, 0, +sin α)** → DX=−cos, DZ=+sin
- liftDir = spanŶ × dragDir, oriented +Z at α=0 = **(+sin α, 0, +cos α)** → LX=+sin, LZ=+cos
- Perpendicular ✓ (dragDir·liftDir = 0), matches verified α=0 baseline (dragDir=(−1,0,0), liftDir=(0,0,1)).

## Settings per campaign (verified correct)

| Setting | AERO | HYDRO |
|---|---|---|
| solver | simpleFoam k-ω SST | simpleFoam k-ω SST |
| ρ (rhoInf) | 1.225 | 1000 |
| ν | 1.5e-5 | 1.0e-6 |
| magUInf | 50 (fixed) | V_w (2–20, per sweep) |
| Aref | 0.075 (fixed ref wing area, all Λ) | 0.075 |
| lRef | 1.021 | 1.021 |
| turbulence | k,ω from 50 m/s, μt/μ=10 | k,ω from V_w, μt/μ=10 |

## −C_p,min post-pass (fills the cavitation gap without re-running)

HYDRO reconstructs the latest-time `p` field to disk. After the batch, extract the suction peak:
```
# for each hydro case: min kinematic pressure over domain → C_p,min = p_min/(0.5 V_w^2)
postProcess -func "fieldMinMax(p)" -latestTime   # writes postProcessing/fieldMinMax(p)/...
```
Run once over all cases; pair p_min with the case's C_L. (Kept out of the live batch to keep it robust.)
