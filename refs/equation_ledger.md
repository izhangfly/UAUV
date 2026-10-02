# Equation ledger

One row per equation extracted from the references. `GP class` ∈ {monomial, posynomial, signomial, non-GP}.
`Handling` ∈ {use as-is, fit→monomial/posynomial, SP, CFD, drop}. `CFD?` = yes if this quantity must come from CFD.

| # | Block | Equation (LaTeX) | Meaning | GP class | Handling | CFD? | Source |
|---|-------|------------------|---------|----------|----------|------|--------|
| _example_ | drag | `$D=\tfrac12\rho V^2 S C_D$` | total drag | monomial (given C_D) | use as-is | — | Renilson §X |
| _example_ | friction | `$C_f=0.075/(\log_{10}Re-2)^2$` | ITTC line | non-GP (log) | fit → `$aRe^{-b}$` | — | ITTC-1957 |
| _example_ | polar | `$C_D=C_{D0}+kC_L^2$` | drag polar | posynomial | use as-is; `k,C_{D0}` from CFD | yes | — |

## Running CFD requirements list (compiled from CFD?=yes rows)
_(single geometry now → scalars/curves over α, Λ, V; generalised → also over d/L, δ/d, c/d, AR)_
- C_D0(Λ), k(Λ)          — drag polar, air & water
- C_Lα(Λ)               — wing lift-curve slope
- C_l(Λ)                — roll coefficient (roll-authority gate)
- −Cp,min(C_L)          — cavitation margin (water)
- a_peak = C·V^a·d^b·m^c — water-entry impact

## Analytic (from books, NOT CFD) — keep these out of the DOE
- friction C_f (ITTC / Schlichting power law), form factor (1+k)(d/L), buoyancy ρ∇,
  added mass (ellipsoid/slender-body), hull buckling p_cr(t/R, L/R), Reynolds, power/energy/range.
