# Entry/exit and volume-size check

## What was changed

- The gas length is now configurable before initialization with
  `/B1/det/gasLength <value> cm`; the transverse size remains 1 m.
- The primary particle's position, momentum, and kinetic energy are recorded
  at the exact World -> GasBox boundary and at the exact GasBox -> World
  boundary.
- The exit state is taken explicitly from the Geant4 post-step point.
- Gas track length and number of gas steps are stored per event.
- A small `StepDebug` tree stores the first ten events, allowing the geometric
  boundary to be distinguished from the first non-zero energy-deposit hit.
- The corrected analysis forms signed projected angles directly:

  `theta_x = atan2(p_x, p_z)`

  `psi_x = atan2(x_out - x_in, z_out - z_in)`

  and similarly for y.
- Full RMS is used for the theta/psi = sqrt(3) transport check. The central-98%
  Gaussian-equivalent theta width is used separately for the PDG core-width
  test.

## Boundary check

For the 100 cm box, the gun starts at z = -510 mm and the gas begins at
z = -500 mm. In the debug events, the vacuum step ends exactly at -500 mm and
has zero direction change. The next step begins exactly at -500 mm and already
accumulates scattering in the gas. Therefore there is no delayed Geant4
scattering start.

The old `Gas` tree records only steps with non-zero deposited energy. Its first
entry can therefore lie tens of millimetres after the boundary; that is a hit
recording delay, not a scattering delay.

## 100k-event volume scan

Particle: mu-, p = 1000 MeV/c. Physics list: FTFP_BERT. The x and y projected
second moments are pooled for the theta/psi result.

| Gas length | Lateral displacement | Downstream events | Geant4 core / PDG | Full-RMS theta/psi | Difference from sqrt(3) | Mean KE loss |
|---:|:---:|---:|---:|---:|---:|---:|
| 25 cm | on | 99,998 | 1.017 | 1.777 | +2.62% | 0.037% |
| 50 cm | on | 99,988 | 1.016 | 1.716 | -0.91% | 0.075% |
| 100 cm | on | 99,983 | 1.015 | 1.726 | -0.35% | 0.149% |
| 100 cm | off | 99,983 | 1.017 | 1.832 | +5.76% | 0.148% |

For the 100 cm production-like configuration with lateral displacement on,
the measured central-core theta is 0.08596 degrees and the PDG prediction is
0.08471 degrees.

## Interpretation

1. Geant4 begins transport in the gas at the geometric boundary; no extra
   starting delay was found.
2. The exit momentum in the new files is unambiguously the boundary post-step
   momentum.
3. With small energy loss and Geant4's normal muon/hadron lateral displacement
   enabled, the 100 cm simulation reproduces the second-moment sqrt(3) relation
   to about 0.35% and the PDG projected core width to about 1.5%.
4. Turning lateral displacement off leaves theta and the PDG comparison almost
   unchanged, but changes psi and spoils the sqrt(3) relation. This confirms
   that psi tests the position-angle transport correlation, not just the final
   scattering angle.
5. The old 50 MeV/c `Muon_z.root` loses roughly half of its kinetic energy. With
   the corrected -500 mm entry point and true Exit position, its full-RMS
   theta/psi ratio is about 2.05, not sqrt(3). It is therefore not a
   constant-scattering-power benchmark.

## Analysis correction relative to the original notebook

- The original source position `[-50, 0, 0]` was inconsistent with Geant4's mm
  position units; the 1 m box entry is -500 mm after the coordinate rotation.
- The original endpoint was the last non-zero energy-deposit hit, not the gas
  boundary.
- The original spherical-angle rotation and 3D/sqrt(2) reconstruction have been
  replaced by the two direct signed projected angles used by the PDG formula.
