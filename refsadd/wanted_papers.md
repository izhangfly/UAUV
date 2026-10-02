# Papers to download for the GP model — by model block

Drop the PDFs here in `~/UAUV/refsadd/`. When you say "add to queue" I'll fold each into the OCR
run (each source → **one** coherent `.mmd`). ✅ open-access / free PDF · 🔒 paywalled (institutional access).
Items marked **(HAVE)** are already in `refs/`.

## A. GP / SP method + data-fitting (the machinery)
- 🔒 Hoburg & Abbeel, "Geometric Programming for Aircraft Design Optimization," AIAA J 2014 — **(HAVE)** https://arc.aiaa.org/doi/10.2514/1.J052732
- ✅ Boyd, Kim, Vandenberghe, Hassibi, "A Tutorial on Geometric Programming," Optim.&Eng. 2007 — **(HAVE)**
- 🔒 Kirschen, Burnell, Hoburg, "Application of Signomial Programming to Aircraft Design," J. Aircraft 2018 — https://arc.aiaa.org/doi/10.2514/1.C034378  *(for the SP parts: buoyancy/trim balance)*
- 🔒 **Hoburg, Kirschen, Abbeel, "Data fitting with GP-compatible softmax functions," Optim.&Eng. 2016** — https://link.springer.com/article/10.1007/s11081-016-9332-3  *(THE gpfit method — how CFD→posynomial)*
- ✅ "The Power of Log Transformation…GP/SP vs NLP for Aircraft Design" — https://www.researchgate.net/publication/322309247

## B. AUV hull drag / body of revolution  → C_D0(d/L), form factor
- 🔒 Myring, "A Theoretical Study of Body Drag in Subcritical Axisymmetric Flow," Aero. Q. 1976 — **(want clean copy)**
- ✅ "Sample-Efficient & Surrogate-Based Design Optimization of Underwater Vehicle Hulls," arXiv 2023 — https://arxiv.org/html/2304.12420v2
- ✅ "Hull shape optimization for AUVs using CFD," Eng. Appl. CFD 2016 — https://www.tandfonline.com/doi/full/10.1080/19942060.2016.1224735
- 🔒 "The effects of head form on resistance… streamlined AUV hull," Ocean Eng 2022 — https://www.sciencedirect.com/science/article/abs/pii/S0029801822009921

## C. Pressure-hull structure  → hoop stress / external-pressure buckling
- 🔒 "Minimum weight design of submersible pressure hull under hydrostatic pressure," Comput.&Struct. 1997 — https://www.sciencedirect.com/science/article/abs/pii/S0045794996003422
- 🔒 "Structural Optimization Applied to Submarine Pressure Hulls," J. Ocean Eng. Mar. Energy 2024 — https://link.springer.com/article/10.1007/s40722-024-00376-4  *(objective = min buoyancy factor; constraints = buckling/yield — maps straight to a GP block)*

## D. Cavitation  → −Cp,min ≤ σ
- ✅ **"Correlation between Pressure Minima and Cavitation Inception Numbers," J. Mar. Sci. Eng. 2022 (MDPI)** — https://www.mdpi.com/2077-1312/10/7/871  *(gives σ_i = −min{Cp}, exactly the GP constraint)*
- 🔒 Brennen, "Cavitation and Bubble Dynamics" — **(HAVE)**

## E. Trans-medium HAUV (vehicle class + folding-wing config, water exit)
- 🔒 "Review of hybrid aerial underwater vehicle: Cross-domain mobility & transitions control," Ocean Eng 2022 — https://www.sciencedirect.com/science/article/abs/pii/S0029801822002840
- ✅ Ma et al., "Configuration Design and Trans-Media Control Status of the HAUV," Appl. Sci. 2022 — **(HAVE)** https://doi.org/10.3390/app12020765
- ✅ **"Novel Design and CFD Analysis of a Foldable Hybrid Aerial Underwater Vehicle," 2024** — https://www.researchgate.net/publication/385762660  *(closest to your folding-wing concept)*
- ✅ "Water-exit dynamics and system identification for a HAUV," Eng. Appl. CFD 2025 — https://www.tandfonline.com/doi/full/10.1080/19942060.2025.2512956  *(the water-EXIT physics you flagged as under-studied)*

## F. Water-entry impact  → a_peak = C·V^a·d^b·m^c
- 🔒 "Experimental investigation of oblique water entry of high-speed truncated cone projectiles: cavity dynamics and impact load," Int. J. Impact Eng 2021 — https://www.sciencedirect.com/science/article/abs/pii/S0889974621000888  *(confirms peak accel ∝ V² — the monomial form)*
- 🔒 "Experimental and numerical study of water entry of projectiles at high oblique entry speed," Ocean Eng 2020 — https://www.sciencedirect.com/science/article/abs/pii/S0029801820305825

## G. Folding / variable-sweep wing aero  → C_L(Λ), lift/drag vs sweep
- ✅ **"Investigation of a Tube-Launched UAV with a Variable-Sweep Wing," Drones 2024 (MDPI)** — https://doi.org/10.3390/drones8090474  *(tube-launched + variable sweep ≈ your launch + skew concept)*
- 🔒 "Morphing aircraft wing variable-sweep: two practical methods & aerodynamic characteristics" — https://www.researchgate.net/publication/286994009

## H. Electric UUV energy / endurance / range  → battery mass, R = V·t
- ✅ "Autonomous Underwater Vehicle Design Considering Energy Source Selection," Southampton thesis — https://eprints.soton.ac.uk/466611/1/1230769.pdf
- 🔒 "Sizing the energy system on long-range AUV," IEEE 2019 — https://ieeexplore.ieee.org/document/8729812
- ✅ Allen et al., REMUS propulsion, OCEANS 2000 — **(HAVE)**

## Added mass / manoeuvring coefficients
Covered by the books already in `refs/`: Newman *Marine Hydrodynamics*, Fossen *Handbook…*, Renilson
*Submarine Hydrodynamics*. Add a dedicated paper only if you want a body-of-revolution added-mass fit.
