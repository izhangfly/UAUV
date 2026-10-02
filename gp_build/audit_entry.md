# Full Audit — ENTRY (water-entry) 2-D interFoam case (2026-08-03)

## The 34-million-g spike had THREE stacked root causes

### Bug E1 — geometry axes swapped (the dominant cause)
`create_nose_stl.py` builds the profile with **x = body axis (±0.5 m span)** and
**z = radius (0–0.1 m)**, then maps 2-D (x,z)→3-D (X,Y,Z). Result: the body sits with its
**axis horizontal (1 m wide in X)** and only **0.1 m tall in Z**. STL bounding box confirms it:
`(-0.5,-0.03,0) → (0.5,0.03,0.1)`. So instead of a slender ogive entering point-first, we built
a **1-metre-wide flat-bottomed hull**. Water rising into a 1 m flat plate at 70 m/s → flat-plate
slamming → ~10–100× too much force. This alone explains most of the 172 kN.
**Fix:** regenerate with axis **vertical (Z = penetration direction)**, radius in X. Body becomes
0.1 m wide, 0.5 m tall, tip at the bottom.

### Bug E2 — body fully submerged at t=0 (the impulsive spike)
`setFieldsDict` fills water for **Z < 0.3**, but the body occupies Z ∈ [0, 0.1]. So at t=0 the
**entire body is already underwater**, surrounded by fluid moving at full V_entry → classic
impulsive-start pressure spike → the peak lands at t≈0 (the 34 M g). 
**Fix:** water fills **Z < 0** only; body sits in AIR above the surface, tip touching at Z=0.
Because the tip is a **point (zero area)**, the t=0 force is ~0 and grows smoothly as the rising
surface wets more of the nose. No impulsive spike — this is the physical entry.

### Bug E3 — a_peak took the global max including startup
Extraction did `max |F|` over all timesteps, so any t≈0 numerical blip won. 
**Fix:** with E2 fixed the force naturally starts at 0; still skip the first few steps and take the
max of the **physical** rise.

## "Is endTime = 0.005 s justified?" — No, not for all cases.

The peak deceleration occurs when the nose has penetrated ≈0.3–0.5 diameter (Wagner slamming
theory: peak of d(wetted area)/dt). Time-to-peak ≈ 0.06 m / V_n, where **V_n = V·sin|θ|** is the
normal penetration speed.

| case | V_n = V·sin\|θ\| | time-to-peak ≈0.06/V_n | 0.005 s enough? |
|---|---|---|---|
| V=70, θ=−75° (fast/steep) | 67.6 m/s | 0.9 ms | yes |
| V=50, θ=−45° | 35.4 m/s | 1.7 ms | yes |
| V=30, θ=−15° (slow/shallow) | 7.8 m/s | 7.7 ms | **NO — 0.005 s cuts off before the peak** |

**Fix:** set endTime **per case** = clamp(0.3 / V_n, 0.004 s, 0.05 s) — captures nose penetration
to ~3 diameters for every (V,θ), and keeps fast cases short. Fixed 0.005 s would silently
truncate the slow/shallow corner of the DOE.

## Other factors checked

| Factor | Finding | Action |
|---|---|---|
| gravity `g` | (0,0,−9.81) correct; body-frame fictitious force neglected (OK for early peak) | keep |
| transportProperties | water ν=1e-6 ρ=1000, air ν=1.48e-5 ρ=1, σ=0.07 — correct two-phase | keep |
| `forces` rho | `rho rho` (phase-aware) — correct for VOF | keep |
| turbulence | laminar — OK, impact is inertia-dominated | keep |
| entry angle θ | encoded via **V_n = V·sin\|θ\|** (normal-velocity governs slam; song2020: tangential effect minor). Sides can stay `slip` (vertical flow is tangential) | simplify to vertical penetration |
| maxCo=0.5, maxAlphaCo=0.5 | fine for VOF impact | keep |
| domain 5 m × 3.5 m | too wide for a 0.1 m body (wastes cells) | shrink to X±0.5, Z[−0.6,0.7] |
| 2-D vs 3-D | 2-D over-predicts (no axisymmetric relief); absorbed by the fitted constant C in a_peak=C·Vⁿ… | note; calibrate C against 1 literature/3-D point |

## Expected result after fix
Physically-correct water entry gives **a_peak ~ 100–1000 g** at these speeds (matches song2020 /
projectile-entry literature). That's *above* the 20 g design gate on purpose — the whole point of
the GP constraint is that raw entry exceeds 20 g and the design (entry angle, nose, structure)
must bring it under. So a_peak in the hundreds of g is the **useful, expected** output, not an error.
