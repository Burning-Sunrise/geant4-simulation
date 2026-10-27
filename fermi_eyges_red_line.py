#!/usr/bin/env python3
"""Reproduce the red Fermi-Eyges curve in the momentum-scan figures.

The curve is semi-analytic: for each incident momentum, it reads the mean
kinetic energy at the true GasBox entry and exit from the Geant4 summary CSV.
It then assumes that the mean kinetic energy decreases linearly with depth and
uses T(s) proportional to 1/[beta(s) p(s)]^2 in the Fermi-Eyges moments.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


MUON_MASS_MEV = 105.6583755
PROJECT = Path(__file__).resolve().parent
INPUT_CSV = (
    PROJECT
    / "momentum_scan_1000000_events"
    / "output"
    / "momentum_scan.csv"
)
OUTPUT_PNG = (
    PROJECT
    / "momentum_scan_1000000_events"
    / "output"
    / "fermi_eyges_red_line_only.png"
)


def fermi_eyges_ratio(entry_ke_mev: float, exit_ke_mev: float) -> float:
    """Return sigma_theta/sigma_psi using a linear mean-energy profile."""
    # u = s/L is normalized depth through the GasBox.
    u = np.linspace(0.0, 1.0, 5001)

    # Geant4 supplies the two endpoint means; the behavior between them is an
    # explicit linear-interpolation assumption of this diagnostic model.
    kinetic_energy = entry_ke_mev + (exit_ke_mev - entry_ke_mev) * u

    # Relativistic kinematics in units with c = 1.
    momentum = np.sqrt(
        kinetic_energy * (kinetic_energy + 2.0 * MUON_MASS_MEV)
    )
    beta = momentum / (kinetic_energy + MUON_MASS_MEV)

    # Only the depth dependence matters in the ratio; common material
    # constants cancel between the two Fermi-Eyges moments.
    scattering_power = 1.0 / (beta * momentum) ** 2

    # Var(theta) is proportional to integral T(u) du.
    theta_variance = np.trapezoid(scattering_power, u)

    # Var(psi) is proportional to integral (1-u)^2 T(u) du.
    psi_variance = np.trapezoid(
        (1.0 - u) ** 2 * scattering_power,
        u,
    )

    return float(math.sqrt(theta_variance / psi_variance))


def main() -> None:
    momenta = []
    ratios = []

    with INPUT_CSV.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            momentum = float(row["momentum_in_MeV_c"])
            entry_ke = float(row["entry_KE_MeV"])
            exit_ke = float(row["mean_exit_KE_MeV"])
            ratio = fermi_eyges_ratio(entry_ke, exit_ke)

            momenta.append(momentum)
            ratios.append(ratio)
            print(
                f"p={momentum:7.1f} MeV/c  "
                f"<K_in>={entry_ke:10.6f} MeV  "
                f"<K_out>={exit_ke:10.6f} MeV  "
                f"ratio={ratio:.6f}"
            )

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.plot(
        momenta,
        ratios,
        "o-",
        color="#d62728",
        lw=2.3,
        label="Fermi-Eyges using Geant4 mean energy loss",
    )
    ax.axhline(
        math.sqrt(3.0),
        color="black",
        ls="--",
        lw=1.8,
        label=r"$\sqrt{3}$",
    )
    ax.set_xscale("log")
    ax.set_xlabel("Incident muon momentum [MeV/c]")
    ax.set_ylabel(r"Predicted $\sigma_\theta/\sigma_\psi$")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUTPUT_PNG, dpi=220)
    plt.close(fig)
    print(f"Wrote {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
