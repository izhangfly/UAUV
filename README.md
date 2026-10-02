# UAUV: Oblique-Wing Aerial-Underwater Vehicle

Design study for a small drone that flies and then dives. It carries a single wing on one central pivot. In the air the wing sits across the body; before entering the water it swings 90 degrees to lie flat along the hull. The targets are 50 m/s in air and a 20 m/s underwater sprint.

The sizing is done with a geometric program (GP), a form of convex optimisation that solves to a global optimum. Wherever the physics can't be written in closed form, CFD supplies the coefficients and they are fitted back into the GP.

## Approach

1. **Sizing model (Layer A).** `uauv_gp_model.py` (GPkit with the cvxopt solver) covers aerodynamics in cruise, hull and wing drag underwater, buoyancy and trim, cavitation, pressure-hull structure, energy and endurance, and water entry. `gp_model.tex` documents every constraint with its source and marks it as GP, signomial, or fitted.
2. **CFD calibration.** The model defines which coefficients it needs, and the CFD campaign is built around that list rather than exploring at random. All runs use OpenFOAM v2606 (steady RANS, k-omega SST):
   - Aerodynamic: 100 cases, 10 wing positions (0 to 90 degrees) by 10 angles of attack.
   - Hydrodynamic: 168 converged cases over wing position, angle of attack and water speed.
   - Cavitation: suction-peak pressure from 40 of the hydrodynamic cases, checked against the cavitation number at 0, 2, 5 and 10 m depth.
   - Water entry: 2D multiphase (interFoam) runs for peak deceleration, in progress.
3. **Fitting.** `cfd/fit_gp.py` turns the CFD results into GP-compatible fits, such as drag polar, lift slope and roll moment as functions of wing position, plus underwater drag against Reynolds number.
4. **Design search (Layer B, planned).** Bayesian optimisation over choices the convex model cannot express, such as the wing-rotation trajectory during the dive.

Reference geometry: 1.021 m hull, 0.10 m diameter; 750 mm by 100 mm wing with a NACA 3612 section. A baseline check on the deployed wing at zero incidence gave C_D = 0.067 and C_L = 0.368.

## Repository layout

- `uauv_gp_model.py`, `gp_model.tex`: the sizing model and its write-up.
- `cfd/`: case templates and batch scripts for the aerodynamic, hydrodynamic, cavitation and water-entry sweeps, plus fitting and plotting.
- `paper/`: paper drafts in the AIAA template, in English and Chinese.
- `gp_build/`: CFD method notes, the sweep plan, nomenclature, and verification reports checking equations, units and citations.
- `refs/`: equation ledger, citation map and BibTeX database.
- `fusion_export_stl.py`: exports the Fusion 360 bodies to watertight STL for meshing.
- `ocr_*.py`, `run_ocr_parallel.sh`: the pipeline used to pull equations out of scanned references.

Mesh files, CFD case outputs, STL exports and compiled PDFs are not committed.

## Built on

- [GPkit](https://github.com/convexengineering/gpkit) and [gplibrary](https://github.com/convexengineering/gplibrary) by Convex Engineering, for the GP formulation and aircraft model patterns.
- [UUV-design-optimization](https://github.com/vardhah/UUV-design-optimization) by Harsh Vardhan and Umesh Timalsina, used as a reference for hull drag optimisation.
- Hoerner, *Fluid-Dynamic Drag* (1965), and the other sources listed in `refs/uauv.bib`, cited in the model rather than reproduced here.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python uauv_gp_model.py
```

The CFD scripts expect an OpenFOAM v2606 environment.
