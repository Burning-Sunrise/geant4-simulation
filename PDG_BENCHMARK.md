# Dedicated PDG-condition benchmark

## Question

Can the Geant4 setup reproduce both

1. the PDG projected multiple-scattering width, and
2. the PDG endpoint relation \(\sigma_\psi=\sigma_\theta/\sqrt{3}\)?

## Conditions chosen to match the PDG approximation

- Uniform He:CO2 = 70:30 gas, 10 atm, 293.15 K.
- Gas length \(L=1\) m and \(x/X_0=0.0163992\).
- A pencil beam enters normally along +z at the centre of the upstream gas face.
- High momenta: 1 GeV/c muons and 5 GeV/c protons.
- Consequently, the mean kinetic-energy losses are only 0.15% and 0.36--0.38%.
- 50,000 events per particle and physics-list setting.
- Only primary particles leaving the downstream face are retained, so every event has the same 1 m material length.
- Muon/hadron lateral displacement is explicitly enabled with
  `/process/msc/MuHadLateralDisplacement true`.
- The two signed one-plane observables are

  \[
  \theta_x=\operatorname{atan2}(p_x,p_z),\qquad
  \psi_x=\operatorname{atan2}(x_{\rm exit}-x_{\rm entry},
                              z_{\rm exit}-z_{\rm entry}),
  \]

  with an identical definition in y.  The entry point is the gas face at
  \(z=-500\) mm, not the particle-gun point at \(-510\) mm.
- Widths are obtained from the central 98% of each projected distribution.
  The RMS of the truncated sample is divided by 0.934553, the analytic
  central-98% truncation factor for a Gaussian.

The PDG prediction used is

\[
\theta_0={13.6\ {\rm MeV}\over \beta p c}\sqrt{x/X_0}
\left[1+0.038\ln\left({x\over X_0\beta^2}\right)\right]
\]

for a singly charged incident particle.

## Results with the original `FTFP_BERT` list

The x/y values below are averaged because they are equivalent projections.

| Particle | Mean energy loss | Geant4 core \(\sigma_\theta\) | PDG \(\theta_0\) | Geant4 / PDG | \(\sigma_\theta/\sigma_\psi\) | Relative to \(\sqrt3\) |
|---|---:|---:|---:|---:|---:|---:|
| muon, 1 GeV/c | 0.149% | 1.498 mrad | 1.478 mrad | 1.013 | 1.773 | 1.023 |
| proton, 5 GeV/c | 0.375% | 0.315 mrad | 0.300 mrad | 1.051 | 1.770 | 1.022 |

Thus the original list reproduces the PDG angular width to 1.3% for muons
and 5.1% for protons.  It reproduces the endpoint \(\sqrt3\) relation to
about 2.3% for both particles.

## Cross-check with `FTFP_BERT_EMY` (EM option 3)

| Particle | Mean energy loss | Geant4 / PDG | \(\sigma_\theta/\sigma_\psi\) | Relative to \(\sqrt3\) |
|---|---:|---:|---:|---:|
| muon, 1 GeV/c | 0.149% | 1.033 | 1.769 | 1.022 |
| proton, 5 GeV/c | 0.361% | 1.042 | 1.768 | 1.021 |

The conclusion is unchanged by this physics-list cross-check.

## Interpretation

Yes: when the observables and beam conditions are made consistent with the
PDG approximation, Geant4 reproduces both the projected angular width and the
\(\sqrt3\) endpoint relation at the few-percent level.

This does not mean the ratio must be exactly \(\sqrt3\) for Sola's original
low-energy files.  In those files, the source coordinate was first mixed in
centimetres and millimetres, and the corrected low-energy tracks still lose a
large fraction of their energy.  Their scattering power therefore increases
strongly along the path, violating the nearly constant-scattering-power
condition behind the simple endpoint relation.

The remaining few-percent offsets in this benchmark should be treated as the
combined scale of the PDG Gaussian approximation, Geant4's condensed spatial
transport, central-core estimator, and physics-model choice.  The proton raw
RMS must not be used as the PDG width because rare nuclear/large-angle events
produce very large tails; PDG explicitly defines the approximation for the
central 98% projected distribution and notes the hadronic contribution.

## Reproduction commands

From `/Users/s.x./Desktop/geant4_project`:

```bash
pixi run B1_copy/build_pixi_validation/exampleB1 B1_copy/pdg_benchmark_mu_z_original.mac FTFP_BERT
pixi run B1_copy/build_pixi_validation/exampleB1 B1_copy/pdg_benchmark_proton_z_original.mac FTFP_BERT
python3 analyze_pdg_benchmark.py \
  --muon /Users/s.x./Data/TPC_Simulation/pdg_benchmark_mu_z_p1000_original_lateral.root \
  --proton /Users/s.x./Data/TPC_Simulation/pdg_benchmark_proton_z_p5000_original_lateral.root \
  --output pdg_benchmark_output/summary_original.csv
```

## Primary references

- Particle Data Group, *Passage of Particles Through Matter*, Sec. 33.3,
  Eqs. 33.15 and 33.18--33.23:
  https://pdg.lbl.gov/2018/reviews/rpp2018-rev-passage-particles-matter.pdf
- L. Eyges, *Multiple Scattering with Energy Loss*, Phys. Rev. 74, 1534
  (1948): https://doi.org/10.1103/PhysRev.74.1534
- N. Kanematsu, *Alternative scattering power for Gaussian beam model of
  heavy charged particles*, NIM B 266 (2008) 5056--5062:
  https://arxiv.org/abs/0806.0106
- Geant4 Physics Reference Manual, *Multiple Scattering*:
  https://geant4.web.cern.ch/documentation/pipelines/master/prm_html/PhysicsReferenceManual/electromagnetic/elastic_scattering/msc.html
