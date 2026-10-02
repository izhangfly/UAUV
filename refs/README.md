# UAUV references — equation-sourcing workflow

**Goal:** source the physics equations for the underwater / trans-medium mission, classify each as
GP-legal or not, and thereby **derive exactly what CFD must supply** (single geometry now; as functions
of geometry when generalising). Then those survive as GP constraints; the rest become CFD/`gpfit` targets.

## Workflow
1. Drop PDFs here in `~/UAUV/refs/`. Born-digital PDFs I can read directly (page ranges).
   Scanned / image PDFs → OCR to LaTeX-preserving Markdown first (see "Conversion" below).
2. Per book/paper I produce a table in `equation_ledger.md`:
   `# | equation (LaTeX) | meaning | GP class | handling | citation`.
3. From the ledger I compile the **CFD requirements list** = every quantity NOT analytically available.
4. Draft the Layer-A GP with placeholders for those → running it prints the exact fits needed → DOE spec.

## Conversion (only for scanned/image PDFs; born-digital I read as-is)
- **marker** (`pip install marker-pdf`) — batch PDF→Markdown, keeps math/tables. Good default.
- **nougat** (Meta) — academic PDF→MMD with LaTeX. Good for papers.
- **Mathpix** — best math OCR (paid); use for tricky/handwritten pages.
- Keep equations as `$...$` LaTeX in the `.md`. Use legitimately obtained copies (library/institutional access).

## Prioritised reading list (get the Tier-1 five first)

### Tier 1 — load-bearing
- **Renilson, *Submarine Hydrodynamics* (Springer, 2nd ed. 2018).** Ch. resistance, appendages, propulsion,
  and a hull-structure overview. One-stop for drag decomposition + appendage drag. → feeds C_D0, form factor, appendage drag.
- **Hoerner, *Fluid-Dynamic Drag* (1965).** Drag coefficients & **form factors in power-law form** (GP-native)
  for streamlined bodies, interference, control surfaces. → form factor `(1+k)(d/L)`, appendage drag.
- **Boyd, Kim, Vandenberghe, Hassibi (2007), "A tutorial on geometric programming," *Optim. Eng.*** The
  definitional reference for monomial/posynomial/signomial + fitting. → cite for every "GP-compatible" claim.
- **Hoburg (2013) PhD thesis, "Aircraft Design Optimization as a Geometric Program."** Fullest worked
  constraint set + max-affine/monomial fitting method. → the template you already half-own.

### Tier 2 — specific blocks
- **Brennen, *Cavitation and Bubble Dynamics* (Oxford; free at Caltech authors.library).** Cavitation number,
  inception, −Cp. → cavitation constraint (−Cp,min is the CFD part).
- **Molland, Turnock, Hudson, *Ship Resistance and Propulsion* (2nd ed.).** ITTC line, form factor, resistance
  components, propulsion. → friction-law fit, resistance build-up.
- **Newman, *Marine Hydrodynamics* (MIT Press, 1977).** Added mass, slender-body. → added mass (analytic, for entry/accel).
- **Fossen, *Handbook of Marine Craft Hydrodynamics and Motion Control* (2011).** 6-DOF EOM, added-mass matrices,
  hydro coefficients. → Layer-B trajectory sim (not GP sizing).
- **Ross, *Pressure Vessels: External Pressure Technology*** (or Renilson hull chapter). → pressure-hull buckling.

### Tier 1/2 — Chinese (HIT-friendly, same size class)
- **李天森《鱼雷操纵性》** — torpedo manoeuvring; added mass, hydrodynamic derivatives, body-of-revolution. Closest size class.
- **施生达《潜艇操纵性》** — submarine manoeuvring, added mass, derivatives.
- **盛振邦、刘应中《船舶原理》(上/下)** — resistance, propulsion, ITTC, form factor (standard CN naval-arch text).
- **潜艇/耐压壳结构** text — pressure-hull external-pressure buckling (中文 formulas).

### Papers (equation-dense, not books)
- **Myring (1976)** "A theoretical study of body drag in subcritical axisymmetric flow" — Myring hull + drag.
- **Allen et al. (2000)** REMUS AUV — worked sizing numbers.
- Long 2025 / Xu 2019 / Ma 2022 (already on Desktop) — water-entry `a_peak`, trajectory.




basic aircraft model:
https://github.com/convexengineering/gplibrary/blob/master/gpkitmodels/SP/SimPleAC/simpleac.pdf

tail boom(might not be useful in this case with my model)
https://github.com/convexengineering/gplibrary/blob/master/gpkitmodels/SP/aircraft/tail/tail_boom_flex.py

cylindrical beam Moment of inertia (might be relevant because my fuseluge is square prism with fillet, like a cylinder? or you should source your own models.)
https://github.com/convexengineering/gplibrary/blob/master/gpkitmodels/misc/Moment%20of%20Inertia%20(cylindrical%20beam)/moi.pdf

atmosphere model, keep this and it might be adaptable to underwater as well. 
https://github.com/convexengineering/gplibrary/blob/master/gpkitmodels/SP/atmosphere/atmosphere.py

wing model. 
https://github.com/convexengineering/gplibrary/blob/master/gpkitmodels/SP/aircraft/wing/wing.py

fuselage model
https://github.com/convexengineering/gplibrary/tree/master/gpkitmodels/GP/aircraft/fuselage

mission model. also check local file /Users/ianzhang/UAUV/mission.png, or as following: 

Overall Concept
The diagram illustrates a hybrid mission profile for a vehicle capable of both flight and underwater operation. The mission is divided into five distinct phases, transitioning the vehicle from a launch platform through the air, into the water, and finally to an underwater cruising state.

Launch Platforms (Phase Start)
The mission can be initiated from one of two platforms:

A₁ (Shipboard platform): The vehicle is launched from a ship or sea-based surface platform.

A₂ (Airborne platform): The vehicle is dropped or launched from an aircraft in flight.

Phase-by-Phase Breakdown

Boosting phase (A₁/A₂ – B):

After launch, the vehicle undergoes a boosting phase where it gains altitude and velocity. This is represented by the steep, dashed red trajectory from the launch points to point B.

Aerial cruising phase (B – C):

Upon reaching point B, the vehicle transitions to horizontal flight. It cruises through the air at a low altitude over a significant distance. The diagram indicates this aerial cruising phase covers a range of 10–30 km.

Diving phase (C – D):

At point C, the vehicle begins a diving maneuver. It angles downward, pitching towards the water's surface (the horizontal axis) in preparation for splashdown. This phase ends at point D, just above or at the water's surface.

Water entry phase (D – E):

This phase involves the vehicle impacting and entering the water. It transitions from an aerial vehicle to an underwater vehicle. The trajectory shows the vehicle submerging and stabilizing its depth.

Underwater cruising phase (E – F):

Once fully submerged and stabilized at point E, the vehicle begins its underwater cruising phase. It travels horizontally underwater. The diagram indicates this underwater phase covers a relatively short range of 1–3 km.

Key Mission Parameters

Total Aerial Range: Approximately 10 to 30 kilometers.

Total Underwater Range: Approximately 1 to 3 kilometers.

Trajectory: The path shows a parabolic boost, a low-altitude glide, a dive, water impact, and a shallow underwater glide.

Use of the following model may be useful, but use the mission profile up there as bible.
https://github.com/convexengineering/gplibrary/tree/master/gpkitmodels/GP/aircraft/mission

Wing structure model, might not be too useful in this study because there involves too many different factors for cruising in water with a wing sideway.
https://github.com/convexengineering/gplibrary/tree/master/gpkitmodels/GP/aircraft/wing

