# Recorded-step Fermi–Eyges comparison

The new scan generates 100,000 muons per momentum, retaining the original
physics configuration and true upstream/downstream selection. Original 1M
ROOT files and plots are untouched.

`G4_STEP_RECORD_EVENTS=100000` enables full primary-step diagnostics. Without
this environment variable the original first-ten-events diagnostic remains.

`analyze_step_energy.py` reconstructs pre/post kinetic energies from each
recorded momentum vector. It integrates T proportional to 1/(beta*p)^2 over
the actual step length using three-point Gaussian quadrature, interpolating
energy only within a step. The displacement weight is ((500-z)/1000)^2.
This retains the small-angle, straight-slab lever-arm approximation of FE;
it is not an exact conditional prediction for Geant4's accepted trajectories.
Material constants cancel for this homogeneous gas.

The reported ratio is sqrt(sum A0 / sum A2), rather than the average of
individual-event ratios. Error bars are block standard errors for the new FE
estimate, and do not include model uncertainties. The blue points remain the
original 1M-event Geant4 analysis, clearly distinguished from the new 100k
energy-profile samples. This tests the energy-profile approximation only;
the scattering-power model itself is unchanged.

## Reproduce

Install Python packages `numpy`, `matplotlib`, and `uproot`, build the Geant4
application as described in INSTALL_PIXI.md, then run from the project root:

```sh
G4_STEP_RECORD_EVENTS=100000 python3 run_momentum_scan.py --events 100000 --threads 4 --scan-label momentum_scan_step_energy_100000
python3 analyze_step_energy.py
```

The output CSV, PNG, and PDF are in `momentum_scan_step_energy_100000/output`.
The 11-point scan shows a change of about 0.00036 at 75 MeV/c and still smaller
changes at 100–200 MeV/c. Thus the whole-slab linear energy interpolation does
not explain the roughly 0.02 residual in that range. At 50 MeV/c the change is
about -0.00490. Generated ROOT files are excluded from Git because of their size.
