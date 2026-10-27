#!/usr/bin/env python3
"""Analyze the dedicated high-energy PDG multiple-scattering benchmark.

Definitions for a +z beam through the 1 m gas slab:
  theta_x,y = atan2(p_x,y, p_z) at the downstream gas face;
  psi_x,y   = atan2(x_exit-x_entry, z_exit-z_entry).

The PDG theta_0 is a one-plane projected angular width.  For a uniform slab
with approximately constant scattering power, the Fermi-Eyges moments give
sigma(theta) / sigma(psi) = sqrt(3).
"""

import argparse
import csv
import math
from pathlib import Path

import numpy as np
import ROOT

ROOT.gROOT.SetBatch(True)

GAS_DENSITY_G_CM3 = 0.00665333
GAS_X0_G_CM2 = 1.0 / (0.175 / 94.32 + 0.225 / 42.70 + 0.600 / 34.24)
SLAB_CM = 100.0
X_OVER_X0 = SLAB_CM * GAS_DENSITY_G_CM3 / GAS_X0_G_CM2
ENTRY_Z_MM = -500.0
EXIT_Z_MM = 500.0
TRUNCATED_98_GAUSSIAN_STD = 0.934553

PARTICLES = {
    "muon": {"mass": 105.6583755, "momentum": 1000.0},
    "proton": {"mass": 938.2720882, "momentum": 5000.0},
}


def load_exit(path):
    root_file = ROOT.TFile.Open(str(path))
    if not root_file or root_file.IsZombie():
        raise OSError(f"Cannot open {path}")
    tree = root_file.Get("Exit")
    if not tree:
        raise KeyError(f"No Exit tree in {path}")
    arrays = ROOT.RDataFrame(tree).AsNumpy()
    return {key: np.asarray(value) for key, value in arrays.items()}


def central98_sigma(values):
    qlo, qhi = np.quantile(values, [0.01, 0.99])
    kept = values[(values >= qlo) & (values <= qhi)]
    return float(np.std(kept, ddof=1) / TRUNCATED_98_GAUSSIAN_STD)


def pdg_theta0(momentum, mass):
    beta = momentum / math.sqrt(momentum**2 + mass**2)
    # PDG/Lynch-Dahl expression for a singly charged particle.  The beta term
    # in the logarithm follows the modern PDG convention used in Sola's deck.
    correction = 1.0 + 0.038 * math.log(X_OVER_X0 / beta**2)
    return 13.6 / (beta * momentum) * math.sqrt(X_OVER_X0) * correction


def analyze(path, particle):
    arrays = load_exit(path)
    # Require the downstream face so every retained primary traversed the full
    # 1 m slab; side exits and upstream backscatter are different path lengths.
    full_slab = arrays["exit_pos_z"] > EXIT_Z_MM - 0.1
    a = {name: values[full_slab] for name, values in arrays.items()}
    if not len(a["KE"]):
        raise RuntimeError(f"No full-slab exits in {path}")

    spec = PARTICLES[particle]
    initial_ke = math.sqrt(spec["momentum"]**2 + spec["mass"]**2) - spec["mass"]
    theta0 = pdg_theta0(spec["momentum"], spec["mass"])
    rows = []
    for coordinate in ("x", "y"):
        theta = np.arctan2(a[f"exit_momentum_{coordinate}"],
                           a["exit_momentum_z"])
        # The incident trajectory enters the gas at (0,0,-500 mm).  The
        # 10 mm world-space flight from the gun at -510 mm is not material.
        psi = np.arctan2(a[f"exit_pos_{coordinate}"],
                         a["exit_pos_z"] - ENTRY_Z_MM)
        theta_sigma = central98_sigma(theta)
        psi_sigma = central98_sigma(psi)
        rows.append({
            "particle": particle,
            "projection": coordinate,
            "input_p_MeV_c": spec["momentum"],
            "n_exit_all": len(arrays["KE"]),
            "n_full_slab": len(a["KE"]),
            "initial_ke_MeV": initial_ke,
            "mean_exit_ke_MeV": float(np.mean(a["KE"])),
            "fractional_ke_loss": (initial_ke - float(np.mean(a["KE"]))) / initial_ke,
            "x_over_X0": X_OVER_X0,
            "theta_core_sigma_mrad": theta_sigma * 1000.0,
            "pdg_theta0_mrad": theta0 * 1000.0,
            "geant_over_pdg": theta_sigma / theta0,
            "psi_core_sigma_mrad": psi_sigma * 1000.0,
            "theta_over_psi": theta_sigma / psi_sigma,
            "sqrt3": math.sqrt(3.0),
            "ratio_over_sqrt3": theta_sigma / psi_sigma / math.sqrt(3.0),
            "corr_theta_psi": float(np.corrcoef(theta, psi)[0, 1]),
            "gaussian_width_rel_stat_error": 1.0 / math.sqrt(2.0 * (len(a["KE"]) - 1)),
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--muon", type=Path, required=True)
    parser.add_argument("--proton", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = analyze(args.muon, "muon") + analyze(args.proton, "proton")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"x/X0 = {X_OVER_X0:.7f}")
    for row in rows:
        print(
            f"{row['particle']:6s} {row['projection']}: "
            f"N={row['n_full_slab']}, dKE/KE={100*row['fractional_ke_loss']:.3f}%, "
            f"theta={row['theta_core_sigma_mrad']:.5f} mrad, "
            f"PDG={row['pdg_theta0_mrad']:.5f} mrad, "
            f"G4/PDG={row['geant_over_pdg']:.4f}, "
            f"theta/psi={row['theta_over_psi']:.4f} "
            f"({row['ratio_over_sqrt3']:.4f}*sqrt(3))"
        )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
