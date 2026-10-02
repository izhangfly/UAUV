# Audit — Layer-A GP model (`uauv_gp_model.py`) vs `gp_model.tex`

Reproduce: `source ~/UAUV/.venv/bin/activate && python3 uauv_gp_model.py`. gpkit 1.1 / cvxopt.

## 1. Constraint-by-constraint mapping (.tex → gpkit)

| gp_model.tex block | gpkit constraint | GP-legal? |
|---|---|---|
| Aerial lift `mg ≤ ½ρ_a V_a² S C_L,a` | `m*g <= 0.5*rho_a*Va**2*S*CLa` | monomial ✓ |
| Aerial stall ceiling | `CLa <= CLmax` (0.60, CFD) | monomial ✓ |
| Aerial polar `C_D,a ≥ …` | `CDa >= kA_aero*CLa**2` (operating-range monomial) | posy ≤ mono ✓ |
| Aerial drag / power | `Da >= ½ρ_a V_a² S CDa`, `Pa >= Da Va/η_a` | monomial ✓ |
| Buoyancy `B=ρ_w g∇` | `B == rho_w*g*vol` | monomial ✓ |
| ξ-trim `mg = B(1+ξ)` | `m*g <= B*(1+ξ)` (ξ fixed per solve) | monomial ✓ |
| Trim lift `L_tr=ξB=½ρ_w V² S_stow C_L,uw` | `Ltr >= ξ*B`, `Ltr <= ½ρ_w V_w² S_stow CLuw` | monomial ✓ |
| Underwater polar `C_D,w ≥ C_D0,w + k_w C_L²` | `CDw >= CD0w + k_w*CLuw**2` | posy ≤ mono ✓ |
| Underwater drag / power | `Dw >= ½ρ_w V_w² S CDw`, `Pw >= Dw V_w/η_w` | monomial ✓ |
| Cavitation `−C_p,min ≤ σ` | `½ρ_w V_w²(−C_p,min) ≤ p_avail` (bounds V_w) | posy ≤ mono ✓ |
| Energy `E_b ≥ P_a t_a + P_w t_w` | `Eb >= Pa*(Ra/Va) + Pw*(Rw/Vw)` | posy ≤ mono ✓ |
| Battery mass | `m_b >= Eb/e_b` | monomial ✓ |
| Hoop stress `t_s ≥ p_d d/2σ_y` | `t_s >= p_d*d/(2σ_y)` | monomial ✓ |
| Buckling `SF·p_d ≤ p_cr` | Windenburg–Trilling monomial `2.42 E (t/d)^2.5 (d/L)` | posy ≤ mono ✓ |
| Skin + structural mass | `m_skin >= ρ_m π d L t_s`, `m_s >= m_skin+m_fins+m_pivot` | posy ≤ mono ✓ |
| Mass closure | `m >= m_pay+m_s+m_b+m_fixed` | posy ≤ mono ✓ |
| Objective max payload | `minimize m_pay**-1` | monomial ✓ |
| **Water-entry a_peak ≤ 20g** | **EXCLUDED — post-hoc `entry_check()`** | (C pending DOE) |
| Roll gate, G_V/G_H stability, QPC decomposition | not yet added (Layer-A skeleton) | — |

**Every included constraint is GP-legal** (posynomial ≤ monomial). The model is a pure GP;
ξ is swept as a parameter (gp_model.tex §buoyancy). If ξ is freed, `mg=B(1+ξ)` becomes signomial
and the model would use `SignomialsEnabled()` + `m.localsolve()` (per gpkit SP docs).

## 2. Approximations / deviations (honest)
1. **Aerial polar as monomial** `C_D,a = 0.55·C_L,a²` — our narrow α-sweep (C_L 0.30–0.57) can't
   support a full posynomial (see `fitted_coefficients.md`); this reproduces the operating range to
   ~15%. Replace once a section-level C_Dp(C_L) or wider sweep is available.
2. **Deployed C_Lα not used directly** — the lift constraint uses the operating C_L,a (weight-set),
   not the (mesh-limited) slope, so the low C_Lα does not corrupt the sizing.
3. **ξ<0 (positively buoyant) branch** collapses to the neutral case (`max(ξ,0)`); the meaningful
   payload frontier is ξ≥0 (heavy vehicle trimmed by the stowed wing).
4. **Entry, roll, stability, propeller-QPC** not in this Layer-A skeleton — entry is post-hoc;
   the others are feasibility gates to add next.

## 3. Sensitivity audit (design point ξ=0.15, all physically correct)
| Driver | d(1/payload) | Reading |
|---|---|---|
| hull volume ∇ | −1.43 | biggest lever — more displacement → more buoyant payload |
| battery e_b | −0.49 | better cells → less battery mass → more payload |
| aerial η_a / R_a | −0.30 / +0.30 | longer/less-efficient aerial leg costs payload |
| V_w,req | +0.38 | faster underwater sprint costs energy → payload |
| C_D0,w | +0.19 | underwater drag moderate |
| k_w | +0.001 | negligible — stowed C_L≈0, confirming CFD |

Dominant binding constraints: **mass closure (+2.02)** and **buoyancy (+1.43)** — the design is
buoyancy-limited, as expected for a near-neutral trans-medium vehicle.

## 4. Solution set (payload–ξ frontier)
Payload rises 2.39 → 3.49 kg as ξ goes 0 → 0.30, bounded above where aerial C_L,a hits the 0.60
stall ceiling. Battery 1.23→1.69 kg, structure 1.28 kg (1.08 mm Al wall at 10 m), P_a≈0.9–1.5 kW,
P_w≈1.5 kW. **The model solves, is bounded, and traces the payload–buoyancy trade the .tex predicts.**
