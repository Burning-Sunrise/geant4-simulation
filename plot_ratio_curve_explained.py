#!/usr/bin/env python3
"""Reproduce the momentum-versus-angle-ratio figure.

Blue points:
    Event-level Geant4 result already summarized in momentum_scan.csv.

Red curve:
    Fermi-Eyges calculation using the Geant4 mean kinetic energies at the
    true gas entry and exit.  The red curve is NOT fitted to the blue points.
    Straight segments only connect independently calculated momentum points.
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
    / "ratio_vs_momentum_reproduced.png"
)


def fermi_eyges_ratio(entry_ke_mev: float, exit_ke_mev: float) -> float:
    """Calculate sigma_theta/sigma_psi for a linear mean-energy profile."""
    # Normalized depth u = s/L, from gas entry (0) to gas exit (1).
    u = np.linspace(0.0, 1.0, 5001)

    # Geant4 supplies <K_in> and <K_out>.  Linear interpolation between them
    # is an explicit approximation in this diagnostic calculation.
    kinetic_energy = entry_ke_mev + (exit_ke_mev - entry_ke_mev) * u

    # Relativistic relations, with c = 1.
    momentum = np.sqrt(
        kinetic_energy * (kinetic_energy + 2.0 * MUON_MASS_MEV)
    )
    beta = momentum / (kinetic_energy + MUON_MASS_MEV)

    # The common material-dependent factor cancels in the ratio, so only
    # the depth dependence T(u) proportional to 1/[beta(u) p(u)]^2 is needed.
    scattering_power = 1.0 / (beta * momentum) ** 2

    # Fermi-Eyges transport moments:
    # Var(theta) proportional to integral T(u) du
    # Var(psi)   proportional to integral (1-u)^2 T(u) du
    theta_variance = np.trapezoid(scattering_power, u)
    psi_variance = np.trapezoid(
        (1.0 - u) ** 2 * scattering_power,
        u,
    )

    return float(math.sqrt(theta_variance / psi_variance))


def main() -> None:
    rows = []
    with INPUT_CSV.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            rows.append(row)

    rows.sort(key=lambda row: float(row["momentum_in_MeV_c"]))

    incident_momentum = np.asarray([
        float(row["momentum_in_MeV_c"]) for row in rows
    ])

    # Blue points and error bars: event-level Geant4 angular analysis.
    geant4_ratio = np.asarray([
        float(row["theta_over_psi"]) for row in rows
    ])
    geant4_ratio_se = np.asarray([
        float(row["theta_over_psi_SE"]) for row in rows
    ])

    # Red points: one independent Fermi-Eyges calculation per momentum.
    red_ratio = np.asarray([
        fermi_eyges_ratio(
            float(row["entry_KE_MeV"]),
            float(row["mean_exit_KE_MeV"]),
        )
        for row in rows
    ])

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.errorbar(
        incident_momentum,
        geant4_ratio,
        yerr=geant4_ratio_se,
        fmt="o",
        capsize=3,
        lw=2,
        color="#1f77b4",
        label="Geant4: signed projected-angle widths",
    )
    ax.plot(
        incident_momentum,
        red_ratio,
        "o-",
        lw=2.3,
        color="#d62728",
        label="Fermi-Eyges using Geant4 mean energy loss (not a fit)",
    )
    ax.axhline(
        math.sqrt(3.0),
        color="black",
        ls="--",
        lw=1.8,
        label=r"Constant scattering power: $\sqrt{3}$",
    )
    ax.set_xscale("log")
    ax.set_xlabel("Incident muon momentum [MeV/c]")
    ax.set_ylabel(r"$\sigma_\theta/\sigma_\psi$")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False, fontsize=10)
    fig.tight_layout()
    fig.savefig(OUTPUT_PNG, dpi=220)
    plt.close(fig)

    for momentum, blue, blue_se, red in zip(
        incident_momentum,
        geant4_ratio,
        geant4_ratio_se,
        red_ratio,
    ):
        print(
            f"p={momentum:7.1f} MeV/c  "
            f"Geant4={blue:.6f} +/- {blue_se:.6f}  "
            f"Fermi-Eyges={red:.6f}"
        )
    print(f"Wrote {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
