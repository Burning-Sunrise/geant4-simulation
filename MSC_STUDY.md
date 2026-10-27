# Geant4-PDG multiple-scattering validation

## The angle-definition issue

The PDG/Highland `theta_0` is the RMS width of **one projected final-direction
angle**, for example `atan(px/pz)` for a beam along +z. It is not a 3D polar
angle. For two equivalent transverse projections, the small-angle 3D RMS is
approximately `sqrt(2) * theta_0`.

The relation `psi_rms = theta_0/sqrt(3)` concerns a different observable:
`psi = atan(transverse endpoint displacement / longitudinal thickness)`. It
follows from integrating zero-mean angular kicks with **constant scattering
power** along a slab. It does not convert a fitted full-track direction into an
exit direction, and it need not hold when the particle loses enough energy that
scattering is much stronger near the downstream end.

## What the existing files show

Direct analysis of the `Exit` tree finds that the x- and z-directed runs agree
within statistical fluctuations. Direction therefore does not matter in the
cubic, homogeneous geometry, as rotational symmetry requires.

The clean validation samples give core projected widths of about 0.48 degrees
for 200 MeV/c muons and 0.122 degrees for 1000 MeV/c protons. The corresponding
PDG predictions are about 0.47 and 0.12 degrees: agreement is at the few-percent
level. (The analysis corrects the RMS of the retained central 98% for Gaussian
truncation.) This directly supports Sven's limited goal: Geant4 and the PDG
formula agree for the non-electron controls in the central multiple-scattering
distribution.

The untrimmed proton RMS is not an appropriate Gaussian-width estimator because
rare large-angle/nuclear scatters dominate it; the PDG formula describes the
central 98% approximation, not those tails.

| sample | projection | Geant4 core sigma (deg) | PDG theta0 (deg) | ratio |
|---|---:|---:|---:|---:|
| muon +z, 200 MeV/c | x | 0.478 | 0.476 | 1.004 |
| muon +z, 200 MeV/c | y | 0.485 | 0.476 | 1.018 |
| muon +x, 200 MeV/c | y | 0.478 | 0.476 | 1.003 |
| muon +x, 200 MeV/c | z | 0.481 | 0.476 | 1.010 |
| proton +z, 1000 MeV/c | x/y | 0.122 | 0.115 | 1.056-1.057 |
| proton +x, 1000 MeV/c | y/z | 0.120-0.122 | 0.115 | 1.042-1.060 |

The existing low-energy runs lose a large fraction of their energy. The
50 MeV/c muons exit with about 5.8 MeV kinetic energy; the existing protons exit
with about 16.9 MeV. Consequently, applying one Highland formula using only the
incident momentum and expecting the uniform-scattering `sqrt(3)` relation is
not a clean PDG-vs-Geant4 test.

## Recommended clean test

1. Use `validate_mu_{x,z}.mac` (200 MeV/c) and
   `validate_proton_{x,z}.mac` (1000 MeV/c). These reduce fractional energy loss
   while retaining measurable scattering.
2. Compare the central 98% RMS of each signed projected exit angle separately
   with PDG `theta_0`. Do not fit the positive 3D polar-angle distribution with
   a zero-mean Gaussian.
3. Treat `theta/psi` as a transport diagnostic, not as the primary PDG test.
4. Repeat with EM option 3/4 and explicit single scattering as a model/step-size
   systematic after the baseline is established.

## Answers to the original questions

### Shoot protons? More muons?

Yes, protons are a useful non-lepton control and were simulated here. For the
central PDG width, 10,000 exits already give roughly 0.7% statistical precision
on a Gaussian sigma, so more baseline muons are not the highest priority. Use
100,000+ only for tail studies or a sub-percent model comparison.

### Does +z versus +x matter?

No measurable physical direction effect was found. The two beam orientations
give the same core widths after permuting coordinates. That is also required by
the cubic homogeneous gas geometry. Keeping one +x sample is a valuable code
check; production scans can use +z only.

### Different physics lists

The study now compares the default EM option 0, faster option 2 (`EMX`), accurate
option 3 (`EMY`), and best-accuracy option 4 (`EMZ`). All preserve the PDG-level
conclusion:

| EM configuration | mean muon core/PDG | mean proton core/PDG |
|---|---:|---:|
| Opt0 baseline | 1.011 | 1.056 |
| EMX / Opt2 | 1.009 | 1.048 |
| EMY / Opt3 | 1.035 | 1.036 |
| EMZ / Opt4 | 1.021 | 1.064 |

Thus the list-related spread is about 3% for the muon and 3% for the proton,
smaller than the original angle-definition discrepancy.

### Geant4 defaults that matter

The Geant4 11.3.2 initialization dump confirms for the baseline `FTFP_BERT`:

- muons and protons use `WentzelVIUni` MSC plus Coulomb scattering;
- MSC step limiting is `Minimal`, with range factor 0.2;
- muon/hadron lateral displacement is disabled;
- ionization step function is `(0.2, 0.1 mm)`;
- the custom gas density is 6.65333 mg/cm3 and its radiation length is
  6097.77 cm, so 1 m corresponds to about 0.0164 radiation lengths.

Turning muon/hadron lateral displacement on changes the endpoint observable
`psi` and moves the central `theta/psi` relation, but leaves the final-angle PDG
comparison essentially unchanged: mean core/PDG is 1.010 for muons and 1.039
for protons. This is evidence that `psi` is transport-model dependent and should
not be used as the primary PDG test.

### Final status of the sqrt(3) issue

It is resolved. The reported ratio near 1.1 is reproduced exactly by a cm/mm
unit mismatch: the gun coordinate `-51 cm` was used numerically as `-51` while
ROOT hit positions are in mm, so the correct source coordinate is `-510 mm`.
After correcting the unit, the ratios become about 2.12 (muon) and 2.03
(proton). They are greater than `sqrt(3)` because the original low-momentum
beams lose a large fraction of their energy, making scattering power increase
toward the exit. A Fermi-Eyges integration using the measured energy change
predicts approximately 2.07 and 2.03. See `SOLA_ANALYSIS_DIAGNOSIS.md` for the
full numerical reproduction.

### Dedicated reproduction of the PDG conditions

A separate high-momentum benchmark now makes the relative kinetic-energy loss
small, uses the gas entrance rather than the gun point for the endpoint angle,
selects only full-length downstream exits, and explicitly enables muon/hadron
lateral displacement.  With the original `FTFP_BERT` list and 50,000 events:

| Particle | mean KE loss | mean core/PDG | mean theta/psi | `(theta/psi)/sqrt(3)` |
|---|---:|---:|---:|---:|
| muon, 1 GeV/c | 0.149% | 1.013 | 1.773 | 1.023 |
| proton, 5 GeV/c | 0.375% | 1.051 | 1.770 | 1.022 |

Therefore Geant4 reproduces both the PDG projected-angle width and the
endpoint `sqrt(3)` relation at the few-percent level when their conditions are
actually imposed.  An `FTFP_BERT_EMY` cross-check gives the same conclusion.
See `PDG_BENCHMARK.md` and `pdg_benchmark_output/` for the full definitions,
commands, and per-projection results.

Run from `B1_copy/build` after rebuilding:

```text
./exampleB1 ../validate_mu_z.mac
./exampleB1 ../validate_mu_x.mac
./exampleB1 ../validate_proton_z.mac
./exampleB1 ../validate_proton_x.mac
```

Analyze without installing uproot (PyROOT is already present):

```text
python3 ../analyze_msc.py /Users/s.x./Data/TPC_Simulation/validation_*.root
```
