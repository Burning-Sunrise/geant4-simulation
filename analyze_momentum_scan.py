#!/usr/bin/env python3
"""Analyze energy loss and Fermi-Eyges moments across a muon momentum scan."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import uproot


MUON_MASS_MEV = 105.6583755
EXPECTED_ENTRY_Z_MM = -500.0
EXPECTED_EXIT_Z_MM = 500.0
TRUNCATED_98_GAUSSIAN_STD = 0.934553


def width(values: np.ndarray) -> float:
    """Population standard deviation, i.e. the full ensemble RMS width."""
    return float(np.std(np.asarray(values), ddof=0))


def pooled_width(x_values: np.ndarray, y_values: np.ndarray) -> float:
    return math.sqrt((width(x_values) ** 2 + width(y_values) ** 2) / 2.0)


def pooled_observables(theta_x, theta_y, psi_x, psi_y):
    theta = pooled_width(theta_x, theta_y)
    psi = pooled_width(psi_x, psi_y)
    return theta, psi, theta / psi


def central98_width(values: np.ndarray) -> float:
    """Gaussian-equivalent sigma from the central 98% of a distribution."""
    values = np.asarray(values)
    qlo, qhi = np.quantile(values, [0.01, 0.99])
    central = values[(values >= qlo) & (values <= qhi)]
    return width(central) / TRUNCATED_98_GAUSSIAN_STD


def pooled_central98_observables(theta_x, theta_y, psi_x, psi_y):
    theta = math.sqrt(
        (central98_width(theta_x) ** 2 + central98_width(theta_y) ** 2) / 2.0
    )
    psi = math.sqrt(
        (central98_width(psi_x) ** 2 + central98_width(psi_y) ** 2) / 2.0
    )
    return theta, psi, theta / psi


def block_errors(
    theta_x, theta_y, psi_x, psi_y, blocks=100, estimator=pooled_observables
):
    indices = np.array_split(np.arange(len(theta_x)), blocks)
    estimates = np.asarray([
        estimator(theta_x[i], theta_y[i], psi_x[i], psi_y[i])
        for i in indices
        if len(i) >= 10
    ])
    return np.std(estimates, axis=0, ddof=1) / math.sqrt(len(estimates))


def fermi_eyges_ratio_from_linear_energy_loss(entry_ke: float, exit_ke: float) -> float:
    """Illustrative ratio using T(s) proportional to 1/[beta(s) p(s)]^2.

    The mean kinetic energy is linearly interpolated between the simulated
    entry and exit means.  This is a transparent diagnostic, not a replacement
    for Geant4's step-by-step transport.
    """
    u = np.linspace(0.0, 1.0, 5001)
    kinetic_energy = entry_ke + (exit_ke - entry_ke) * u
    momentum = np.sqrt(kinetic_energy * (kinetic_energy + 2.0 * MUON_MASS_MEV))
    beta = momentum / (kinetic_energy + MUON_MASS_MEV)
    scattering_power = 1.0 / (beta * momentum) ** 2
    theta_variance = np.trapezoid(scattering_power, u)
    psi_variance = np.trapezoid((1.0 - u) ** 2 * scattering_power, u)
    return float(np.sqrt(theta_variance / psi_variance))


def analyze_file(path: Path, max_events: int | None = None) -> dict[str, float]:
    match = re.search(r"_p([0-9]+(?:\.[0-9]+)?)_", path.name)
    if not match:
        raise ValueError(f"Momentum missing from filename: {path.name}")
    momentum = float(match.group(1))

    branches = [
        "Event_no", "KE", "entry_KE", "entered",
        "entry_momentum_x", "entry_momentum_y", "entry_momentum_z",
        "exit_momentum_x", "exit_momentum_y", "exit_momentum_z",
        "entry_pos_x", "entry_pos_y", "entry_pos_z",
        "exit_pos_x", "exit_pos_y", "exit_pos_z",
    ]
    with uproot.open(path) as root_file:
        arrays = root_file["Exit"].arrays(branches, library="np")

    valid = (
        (arrays["entered"] == 1)
        & np.isclose(arrays["entry_pos_z"], EXPECTED_ENTRY_Z_MM, atol=1e-6)
        & np.isclose(arrays["exit_pos_z"], EXPECTED_EXIT_Z_MM, atol=1e-6)
    )
    if max_events is not None:
        valid &= arrays["Event_no"] < max_events
    a = {key: np.asarray(value)[valid] for key, value in arrays.items()}
    if len(a["Event_no"]) < 100:
        raise RuntimeError(f"Too few downstream events in {path.name}")

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

    theta, psi, ratio = pooled_observables(theta_x, theta_y, psi_x, psi_y)
    theta_err, psi_err, ratio_err = block_errors(theta_x, theta_y, psi_x, psi_y)
    theta98, psi98, ratio98 = pooled_central98_observables(
        theta_x, theta_y, psi_x, psi_y
    )
    theta98_err, psi98_err, ratio98_err = block_errors(
        theta_x,
        theta_y,
        psi_x,
        psi_y,
        estimator=pooled_central98_observables,
    )

    p_exit = np.sqrt(
        a["exit_momentum_x"] ** 2
        + a["exit_momentum_y"] ** 2
        + a["exit_momentum_z"] ** 2
    )
    entry_ke = float(np.mean(a["entry_KE"]))
    exit_ke = float(np.mean(a["KE"]))
    exit_p = float(np.mean(p_exit))

    return {
        "momentum_in_MeV_c": momentum,
        "events_generated": (
            min(max_events, int(np.max(arrays["Event_no"])) + 1)
            if max_events is not None
            else int(np.max(arrays["Event_no"])) + 1
        ),
        "events_downstream": len(a["Event_no"]),
        "entry_KE_MeV": entry_ke,
        "mean_exit_KE_MeV": exit_ke,
        "KE_loss_MeV": entry_ke - exit_ke,
        "fractional_KE_loss": (entry_ke - exit_ke) / entry_ke,
        "mean_exit_momentum_MeV_c": exit_p,
        "fractional_momentum_loss": (momentum - exit_p) / momentum,
        "theta_plane_RMS_deg": math.degrees(theta),
        "theta_plane_RMS_SE_deg": math.degrees(theta_err),
        "psi_plane_RMS_deg": math.degrees(psi),
        "psi_plane_RMS_SE_deg": math.degrees(psi_err),
        "theta_over_psi": ratio,
        "theta_over_psi_SE": ratio_err,
        "theta_plane_central98_sigma_deg": math.degrees(theta98),
        "theta_plane_central98_sigma_SE_deg": math.degrees(theta98_err),
        "psi_plane_central98_sigma_deg": math.degrees(psi98),
        "psi_plane_central98_sigma_SE_deg": math.degrees(psi98_err),
        "central98_theta_over_psi": ratio98,
        "central98_theta_over_psi_SE": ratio98_err,
        "fermi_eyges_linear_loss_prediction": fermi_eyges_ratio_from_linear_energy_loss(
            entry_ke, exit_ke
        ),
        "ratio_minus_sqrt3_percent": 100.0 * (ratio / math.sqrt(3.0) - 1.0),
    }


def save_csv(rows: list[dict[str, float]], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_results(rows: list[dict[str, float]], output_dir: Path) -> None:
    p = np.asarray([row["momentum_in_MeV_c"] for row in rows])
    ke_loss = 100.0 * np.asarray([row["fractional_KE_loss"] for row in rows])
    momentum_loss = 100.0 * np.asarray([row["fractional_momentum_loss"] for row in rows])
    theta = np.asarray([row["theta_plane_RMS_deg"] for row in rows])
    theta_err = np.asarray([row["theta_plane_RMS_SE_deg"] for row in rows])
    psi = np.asarray([row["psi_plane_RMS_deg"] for row in rows])
    psi_err = np.asarray([row["psi_plane_RMS_SE_deg"] for row in rows])
    ratio = np.asarray([row["theta_over_psi"] for row in rows])
    ratio_err = np.asarray([row["theta_over_psi_SE"] for row in rows])
    predicted_ratio = np.asarray([
        row["fermi_eyges_linear_loss_prediction"] for row in rows
    ])
    ratio98 = np.asarray([row["central98_theta_over_psi"] for row in rows])
    ratio98_err = np.asarray([row["central98_theta_over_psi_SE"] for row in rows])
    theta98 = np.asarray([row["theta_plane_central98_sigma_deg"] for row in rows])
    theta98_err = np.asarray([
        row["theta_plane_central98_sigma_SE_deg"] for row in rows
    ])
    psi98 = np.asarray([row["psi_plane_central98_sigma_deg"] for row in rows])
    psi98_err = np.asarray([
        row["psi_plane_central98_sigma_SE_deg"] for row in rows
    ])

    plt.rcParams.update({"font.size": 13, "axes.spines.top": False, "axes.spines.right": False})

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.plot(p, ke_loss, "o-", lw=2, label="Kinetic-energy loss")
    ax.plot(p, momentum_loss, "s-", lw=2, label="Momentum loss")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Incident muon momentum [MeV/c]")
    ax.set_ylabel("Mean fractional loss [%]")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "01_energy_loss_vs_momentum.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.errorbar(p, theta, yerr=theta_err, fmt="o-", capsize=3, lw=2, label=r"$\theta_{\rm plane}$")
    ax.errorbar(p, psi, yerr=psi_err, fmt="s-", capsize=3, lw=2, label=r"$\psi_{\rm plane}$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Incident muon momentum [MeV/c]")
    ax.set_ylabel("Full-RMS angular width [deg]")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "02_angles_vs_momentum.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.errorbar(p, ratio, yerr=ratio_err, fmt="o", capsize=3, lw=2,
                color="#1f77b4", label="Geant4 full RMS")
    ax.plot(p, predicted_ratio, "-", lw=2.3, color="#d62728",
            label="Fermi-Eyges using Geant4 mean energy loss")
    ax.axhline(math.sqrt(3.0), color="black", ls="--", lw=1.8, label=r"$\sqrt{3}$")
    ax.set_xscale("log")
    ax.set_xlabel("Incident muon momentum [MeV/c]")
    ax.set_ylabel(r"$\sigma_\theta/\sigma_\psi$")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "03_ratio_vs_momentum.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.errorbar(ke_loss, ratio, yerr=ratio_err, fmt="o", capsize=3,
                color="#1f77b4", label="Geant4 full RMS")
    order = np.argsort(ke_loss)
    ax.plot(ke_loss[order], predicted_ratio[order], "-", lw=2.3,
            color="#d62728", label="Fermi-Eyges using Geant4 mean energy loss")
    for x_value, y_value, momentum in zip(ke_loss, ratio, p):
        ax.annotate(f"{momentum:g}", (x_value, y_value), xytext=(5, 5), textcoords="offset points", fontsize=9)
    ax.axhline(math.sqrt(3.0), color="black", ls="--", lw=1.8, label=r"$\sqrt{3}$")
    ax.set_xscale("log")
    ax.set_xlabel("Mean kinetic-energy loss [%]")
    ax.set_ylabel(r"$\sigma_\theta/\sigma_\psi$")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "04_ratio_vs_energy_loss.png", dpi=220)
    plt.close(fig)

    u = np.linspace(0.0, 1.0, 500)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.plot(u, np.ones_like(u), lw=3, label=r"Weight in $\mathrm{Var}(\theta)$: 1")
    ax.plot(u, (1.0 - u) ** 2, lw=3, label=r"Weight in $\mathrm{Var}(\psi)$: $(1-s/L)^2$")
    ax.set_xlabel(r"Normalized depth $s/L$")
    ax.set_ylabel("Geometric weight")
    ax.set_ylim(-0.03, 1.08)
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "05_transport_weights.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.errorbar(p, ratio98, yerr=ratio98_err, fmt="o", capsize=3, lw=2,
                color="#1f77b4", label="Geant4 central-98% Gaussian-equivalent width")
    ax.plot(p, predicted_ratio, "-", lw=2.3, color="#d62728",
            label="Fermi-Eyges using Geant4 mean energy loss")
    ax.axhline(math.sqrt(3.0), color="black", ls="--", lw=1.8, label=r"$\sqrt{3}$")
    ax.set_xscale("log")
    ax.set_xlabel("Incident muon momentum [MeV/c]")
    ax.set_ylabel(r"$\sigma_\theta/\sigma_\psi$")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "06_ratio_vs_momentum_central98.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.errorbar(ke_loss, ratio98, yerr=ratio98_err, fmt="o", capsize=3,
                color="#1f77b4", label="Geant4 central-98% Gaussian-equivalent width")
    order = np.argsort(ke_loss)
    ax.plot(ke_loss[order], predicted_ratio[order], "-", lw=2.3,
            color="#d62728", label="Fermi-Eyges using Geant4 mean energy loss")
    for x_value, y_value, momentum in zip(ke_loss, ratio98, p):
        ax.annotate(f"{momentum:g}", (x_value, y_value), xytext=(5, 5),
                    textcoords="offset points", fontsize=9)
    ax.axhline(math.sqrt(3.0), color="black", ls="--", lw=1.8, label=r"$\sqrt{3}$")
    ax.set_xscale("log")
    ax.set_xlabel("Mean kinetic-energy loss [%]")
    ax.set_ylabel(r"$\sigma_\theta/\sigma_\psi$")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "07_ratio_vs_energy_loss_central98.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.errorbar(p, theta98, yerr=theta98_err, fmt="o-", capsize=3, lw=2,
                label=r"$\sigma_\theta$ (central 98%)")
    ax.errorbar(p, psi98, yerr=psi98_err, fmt="s-", capsize=3, lw=2,
                label=r"$\sigma_\psi$ (central 98%)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Incident muon momentum [MeV/c]")
    ax.set_ylabel("Gaussian-equivalent angular width [deg]")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "08_angles_vs_momentum_central98.png", dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Use only generated events with Event_no below this value.",
    )
    parser.add_argument(
        "--scan-dir",
        default="momentum_scan",
        help="Scan directory name under the project directory.",
    )
    args = parser.parse_args()

    project = Path(__file__).resolve().parent
    scan_dir = project / args.scan_dir
    root_files = sorted(
        (scan_dir / "root").glob("muon_p*_L100_true_boundaries.root"),
        key=lambda path: float(re.search(r"_p([0-9.]+)_", path.name).group(1)),
    )
    if not root_files:
        raise SystemExit("No momentum-scan ROOT files found. Run run_momentum_scan.py first.")

    rows = [analyze_file(path, max_events=args.max_events) for path in root_files]
    output_name = "output" if args.max_events is None else f"output_{args.max_events}_events"
    output_dir = scan_dir / output_name
    output_dir.mkdir(parents=True, exist_ok=True)
    save_csv(rows, output_dir / "momentum_scan.csv")
    plot_results(rows, output_dir)

    print("p [MeV/c]  KE loss [%]  theta [deg]  psi [deg]  theta/psi")
    for row in rows:
        print(
            f"{row['momentum_in_MeV_c']:9.0f}  "
            f"{100*row['fractional_KE_loss']:11.4f}  "
            f"{row['theta_plane_RMS_deg']:11.6f}  "
            f"{row['psi_plane_RMS_deg']:9.6f}  "
            f"{row['theta_over_psi']:9.4f} +/- {row['theta_over_psi_SE']:.4f}"
        )


if __name__ == "__main__":
    main()
