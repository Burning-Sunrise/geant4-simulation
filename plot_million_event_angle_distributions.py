#!/usr/bin/env python3
"""Plot signed projected-angle distributions from the 1M-event scan.

Each incident momentum produces one 2x2 figure containing theta_x, theta_y,
psi_x, and psi_y.  The black histogram uses all valid downstream events in
the displayed central range.  The red curve is a Gaussian whose width is the
Gaussian-equivalent central-98% sigma; it is a visual core comparison, not a
fit to the tails.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import ROOT


PROJECT = Path(__file__).resolve().parent
SCAN_DIR = PROJECT / "momentum_scan_1000000_events"
ROOT_DIR = SCAN_DIR / "root"
OUTPUT_DIR = SCAN_DIR / "output" / "angle_distributions_1M"
EXPECTED_ENTRY_Z_MM = -500.0
EXPECTED_EXIT_Z_MM = 500.0
TRUNCATED_98_GAUSSIAN_STD = 0.934553


def momentum_from_name(path: Path) -> float:
    match = re.search(r"_p([0-9]+(?:\.[0-9]+)?)_", path.name)
    if not match:
        raise ValueError(f"Momentum missing from filename: {path.name}")
    return float(match.group(1))


def central98_gaussian_parameters(values: np.ndarray) -> tuple[float, float]:
    qlo, qhi = np.quantile(values, [0.01, 0.99])
    central = values[(values >= qlo) & (values <= qhi)]
    mean = float(np.mean(central))
    sigma = float(np.std(central, ddof=0) / TRUNCATED_98_GAUSSIAN_STD)
    return mean, sigma


def gaussian_pdf(x: np.ndarray, mean: float, sigma: float) -> np.ndarray:
    return np.exp(-0.5 * ((x - mean) / sigma) ** 2) / (
        math.sqrt(2.0 * math.pi) * sigma
    )


def load_angles(path: Path) -> tuple[dict[str, np.ndarray], int]:
    branches = [
        "entered",
        "entry_momentum_x",
        "entry_momentum_y",
        "entry_momentum_z",
        "exit_momentum_x",
        "exit_momentum_y",
        "exit_momentum_z",
        "entry_pos_x",
        "entry_pos_y",
        "entry_pos_z",
        "exit_pos_x",
        "exit_pos_y",
        "exit_pos_z",
    ]
    frame = ROOT.RDataFrame("Exit", str(path))
    arrays = {
        key: np.asarray(value)
        for key, value in frame.AsNumpy(branches).items()
    }
    valid = (
        (arrays["entered"] == 1)
        & np.isclose(
            arrays["entry_pos_z"], EXPECTED_ENTRY_Z_MM, atol=1.0e-6
        )
        & np.isclose(
            arrays["exit_pos_z"], EXPECTED_EXIT_Z_MM, atol=1.0e-6
        )
    )
    a = {key: value[valid] for key, value in arrays.items()}

    theta_x = (
        np.arctan2(a["exit_momentum_x"], a["exit_momentum_z"])
        - np.arctan2(a["entry_momentum_x"], a["entry_momentum_z"])
    )
    theta_y = (
        np.arctan2(a["exit_momentum_y"], a["exit_momentum_z"])
        - np.arctan2(a["entry_momentum_y"], a["entry_momentum_z"])
    )
    dz = a["exit_pos_z"] - a["entry_pos_z"]
    psi_x = np.arctan2(a["exit_pos_x"] - a["entry_pos_x"], dz)
    psi_y = np.arctan2(a["exit_pos_y"] - a["entry_pos_y"], dz)

    angles_deg = {
        r"$\theta_x$": np.degrees(theta_x),
        r"$\theta_y$": np.degrees(theta_y),
        r"$\psi_x$": np.degrees(psi_x),
        r"$\psi_y$": np.degrees(psi_y),
    }
    return angles_deg, int(np.count_nonzero(valid))


def plot_file(path: Path, output_dir: Path) -> Path:
    momentum = momentum_from_name(path)
    angles, valid_events = load_angles(path)

    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.6))
    for ax, (label, values) in zip(axes.flat, angles.items()):
        mean, sigma = central98_gaussian_parameters(values)
        low, high = np.quantile(values, [0.001, 0.999])
        extent = max(abs(float(low)), abs(float(high)))
        plot_range = (-extent, extent)

        ax.hist(
            values,
            bins=150,
            range=plot_range,
            density=True,
            histtype="step",
            lw=1.7,
            color="black",
            label="Geant4 events",
        )
        x = np.linspace(*plot_range, 1000)
        ax.plot(
            x,
            gaussian_pdf(x, mean, sigma),
            color="#d62728",
            lw=2.2,
            label="Central-98% Gaussian core",
        )
        ax.axvline(0.0, color="0.5", ls="--", lw=1.0)
        ax.set_title(
            rf"{label}: $\mu={mean:.4g}^\circ$, "
            rf"$\sigma_{{98}}={sigma:.4g}^\circ$"
        )
        ax.set_xlabel(f"signed {label} [deg]")
        ax.set_ylabel("probability density")
        ax.grid(True, alpha=0.18)

    axes[0, 0].legend(frameon=False, fontsize=9)
    fig.suptitle(
        f"Muon +z, p = {momentum:g} MeV/c, 1,000,000 generated events\n"
        f"{valid_events:,} events cross the true GasBox entry and downstream exit",
        fontsize=15,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.93))

    output = output_dir / f"angle_distributions_p{momentum:g}_1M.png"
    fig.savefig(output, dpi=220)
    plt.close(fig)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--momentum",
        type=float,
        action="append",
        help="Only plot this momentum in MeV/c; repeat for multiple values.",
    )
    args = parser.parse_args()

    files = sorted(ROOT_DIR.glob("muon_p*_L100_true_boundaries.root"),
                   key=momentum_from_name)
    if args.momentum:
        requested = set(args.momentum)
        files = [p for p in files if momentum_from_name(p) in requested]
    if not files:
        raise FileNotFoundError("No matching 1M-event ROOT files found")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in files:
        output = plot_file(path, OUTPUT_DIR)
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
