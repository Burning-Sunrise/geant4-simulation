# Energy-loss explanation and muon momentum scan

## Main conclusion

Energy loss does **not** affect the exit-direction angle and endpoint-displacement
angle in the same way.  The reason is geometric: scattering at depth `s`
contributes with weight 1 to the final direction, but with weight
`(L-s)^2/L^2` to the endpoint-displacement variance.  When a particle loses
energy, the scattering power grows toward the downstream end.  This late
scattering strongly increases `theta`, but has little remaining lever arm to
increase `psi`, so `sigma_theta/sigma_psi` rises above `sqrt(3)`.

The new scan shows that the original 50 MeV/c muons are strongly affected:
their mean kinetic-energy loss is 47.7% and their measured full-RMS ratio is
2.085.  At 1 GeV/c the mean kinetic-energy loss is only 0.148%.  The
energy-loss-only Fermi-Eyges estimate is then 1.7326, essentially equal to
`sqrt(3) = 1.7321`.  Raising the momentum beyond 1 GeV/c therefore does not
materially improve the **energy-loss** approximation; remaining scatter in the
measured ratios comes from finite statistics, non-Gaussian tails, and transport
model details rather than insufficient momentum.

## Origin of the two formulas

Work in one projected plane.  Let `dtheta(s)` be the small random angular kick
received in a path element `ds`.  Define the scattering power

```text
T(s) = d Var(theta) / ds.
```

Equivalently,

```text
E[dtheta(s)] = 0,
Var[dtheta(s)] = T(s) ds.
```

Assuming independent small-angle increments, the exit angle is the sum of all
kicks:

```text
theta(L) = integral_0^L dtheta(s).
```

Independent variances add, giving

```text
Var(theta) = integral_0^L T(s) ds.
```

A kick at position `s` changes the direction for only the remaining distance
`L-s`, so its contribution to the exit displacement is

```text
dy(L) = (L-s) dtheta(s).
```

Therefore

```text
y(L) = integral_0^L (L-s) dtheta(s),
psi approximately equals y(L)/L,
Var(psi) = (1/L^2) integral_0^L (L-s)^2 T(s) ds.
```

These are the Fermi-Eyges transport moments.  They follow directly from
small-angle stochastic transport and are not an empirical correction invented
for this analysis.

For constant scattering power `T(s)=T0`,

```text
Var(theta) = T0 L,
Var(psi) = T0 L/3,
sigma_theta/sigma_psi = sqrt(3).
```

## Meaning of the physical quantities

- `s`: path depth measured from the material entrance.
- `L`: total material thickness along the nominal beam direction; here 1 m.
- `theta`: signed projected exit-direction angle relative to the entrance
  direction.
- `y(L)`: projected transverse displacement between the material entrance and
  exit.
- `psi`: endpoint-displacement angle, approximately `y(L)/L` at small angles.
- `T(s)`: scattering power, the angular variance accumulated per unit path
  length in one projected plane.
- `p(s)`: local momentum after any energy loss accumulated before depth `s`.
- `beta(s)`: local speed divided by the speed of light.

To leading order,

```text
T(s) is proportional to 1 / [beta(s) p(s)]^2.
```

Thus, energy loss lowers `p(s)` and `beta(s)` and raises the downstream
scattering power.

## Authority and scope

- L. Eyges, *Multiple Scattering with Energy Loss*, Physical Review 74, 1534
  (1948), DOI 10.1103/PhysRev.74.1534, is the original energy-loss-aware
  transport treatment.
- B. Gottschalk, arXiv:0908.1413, explicitly defines scattering power as the
  derivative of the mean squared projected multiple-scattering angle and
  reviews its use in Fermi-Eyges transport.
- The Particle Data Group, *Passage of Particles Through Matter*, Sec. 34.3,
  gives the projected angular width `theta_0` and the constant-scattering-power
  endpoint relation.  The single-value PDG expression uses incident `p` and
  `beta`; it does not perform the depth integral with an evolving momentum.

The two integral formulas use the Gaussian/small-angle transport approximation.
Rare single-scattering tails and detailed Geant4 step algorithms can make a
finite-sample full RMS fluctuate around the ideal prediction.

## Simulation scan

Common settings:

- 30,000 generated muons per momentum point.
- `mu-`, incident along `+z`.
- 1 m He:CO2 gas box at 10 atm.
- FTFP_BERT physics list.
- Geant4 muon/hadron lateral displacement enabled.
- `theta` and `psi` calculated from the true recorded entry and exit boundary
  states.
- Full RMS pooled across the x and y projected planes.

| p [MeV/c] | Mean KE loss | theta RMS [deg] | psi RMS [deg] | Geant4 theta/psi | Energy-loss-only estimate |
|---:|---:|---:|---:|---:|---:|
| 50 | 47.709% | 5.9193 | 2.8395 | 2.0846 +/- 0.0101 | 2.0547 |
| 75 | 11.143% | 2.3797 | 1.3301 | 1.7892 +/- 0.0145 | 1.7806 |
| 100 | 4.876% | 1.4854 | 0.8174 | 1.8172 +/- 0.0257 | 1.7515 |
| 150 | 1.864% | 0.8332 | 0.4939 | 1.6868 +/- 0.0206 | 1.7390 |
| 200 | 1.077% | 0.5556 | 0.3247 | 1.7112 +/- 0.0162 | 1.7360 |
| 300 | 0.574% | 0.3654 | 0.2028 | 1.8021 +/- 0.0368 | 1.7341 |
| 500 | 0.305% | 0.2113 | 0.1171 | 1.8044 +/- 0.0208 | 1.7332 |
| 750 | 0.199% | 0.1379 | 0.0756 | 1.8227 +/- 0.0335 | 1.7328 |
| 1000 | 0.148% | 0.1102 | 0.0637 | 1.7294 +/- 0.0165 | 1.7326 |
| 1500 | 0.099% | 0.0676 | 0.0380 | 1.7802 +/- 0.0290 | 1.7325 |
| 2000 | 0.075% | 0.0510 | 0.0286 | 1.7845 +/- 0.0251 | 1.7324 |

The energy-loss-only estimate uses the simulated mean entry and exit kinetic
energies, a linear mean energy profile, and
`T(s) proportional to 1/[beta(s)p(s)]^2`.  It is included to isolate the
energy-loss mechanism; it is not a substitute for Geant4 transport.

## Suggested slide sequence

1. **Why equal cancellation is not correct** - display the two transport
   integrals and highlight the extra `(L-s)^2` factor for `psi`.
2. **Physical picture** - use `05_transport_weights.png`; late scattering has
   full weight in `theta` but almost zero weight in `psi`.
3. **Momentum controls energy loss** - use `01_energy_loss_vs_momentum.png`.
4. **Both angles shrink with momentum** - use `02_angles_vs_momentum.png`.
5. **The ratio approaches the constant-power limit** - use
   `03_ratio_vs_momentum.png`, showing the smooth energy-loss prediction and
   Geant4 points.
6. **Decision** - 1 GeV/c is sufficient for suppressing the energy-loss bias;
   use at least 100k events for a tail-sensitive sub-percent RMS test.
