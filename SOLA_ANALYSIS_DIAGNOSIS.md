# Reproduction and diagnosis of Sola's theta/psi result

## Exact reproduction

The June 3 slides define:

- `theta_plane`: projected angle between exit momentum and the +z incident
  direction;
- `psi_plane`: projected angle between the vector from the source to the last
  gas hit and the +z direction.

Using the supplied ROOT files, the slide values are reproduced when the source
coordinate is inserted numerically as `z_source = -51` while hit/exit positions
are stored by Geant4 in mm:

| sample and central fit | psi x/y (deg) | theta x/y (deg) | mean theta/psi |
|---|---:|---:|---:|
| 10k muons, central 98% | 4.65 / 4.62 | 5.31 / 5.44 | 1.158 |
| 10k protons, central 96% | 1.75 / 1.79 | 1.95 / 1.94 | 1.100 |

These reproduce the reported 4.63, 5.36, 1.76, and 1.945 degree values.

## Root cause

The gun macro uses `-51 cm`, but Geant4 analysis positions are written in its
default length unit, mm. Therefore the same physical source coordinate is
`-510 mm`, not `-51 mm`.

The erroneous denominator for the source-to-exit chord is approximately

`500 - (-51) = 551 mm`,

instead of approximately

`500 - (-510) = 1010 mm`.

This makes `psi` almost twice too large and drives `theta/psi` from about 2.1
down to the reported 1.1. Increasing the sample from 10k to 100k does not fix a
unit error: the supplied 100k muon sample gives 1.156 with the wrong source and
2.114 with the corrected source.

For the slab-displacement formula, the most physical reference is actually the
gas entry plane at `z = -500 mm`, with material thickness `L = 1000 mm`, rather
than the gun point 10 mm outside the gas.

## Why the corrected ratio is not sqrt(3)

The `sqrt(3)` result assumes constant scattering power along the slab. In
Fermi-Eyges notation,

`<theta^2> = integral T(s) ds`

and

`<y^2> = integral (L-s)^2 T(s) ds`.

Only for constant `T` does this reduce to

`psi_rms = y_rms/L = theta_rms/sqrt(3)`.

The original low-energy beams lose a large fraction of their kinetic energy:
the 50 MeV/c muon begins at 11.23 MeV and exits near 5.74 MeV, while the
242 MeV/c proton begins near 30.71 MeV and exits near 16.91 MeV. Because
scattering power grows roughly as `1/(beta*p)^2`, scattering is stronger near
the exit, where it changes final direction but has little remaining lever arm
to create endpoint displacement.

A simple energy-loss-aware integration with kinetic energy decreasing linearly
between the measured endpoints predicts:

- muon `theta/psi` about 2.07;
- proton `theta/psi` about 2.03.

The corrected ROOT results are about 2.12 and 2.03, respectively. Thus the
post-fix ratios are consistent with the expected non-uniform-scattering effect.

## Required code correction

Use one consistent unit system. Either:

```python
# ROOT positions kept in mm
source = np.array([0.0, 0.0, -510.0])
```

or:

```python
# Convert ROOT positions from mm to cm
hit_position_cm = hit_position_mm / 10.0
source_cm = np.array([0.0, 0.0, -51.0])
```

For comparison with the slab displacement relation, prefer the entry-to-exit
chord with `entry = (0, 0, -500 mm)` and use the recorded `Exit` position,
rather than the last ionization hit.

## Consequence for the PDG validation

The unit bug affects `psi`, not the exit-momentum angle `theta`. Sven's limited
PDG test should compare the signed projected exit-angle core directly with PDG
`theta_0`. The higher-momentum validation samples remain the clean control
because their fractional energy loss is much smaller.
