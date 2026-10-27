#!/usr/bin/env python3
"""Analyze entry/exit-based Geant4 multiple-scattering checks.

The PDG observable is a signed projected exit-direction angle.  The endpoint
angle is formed from the recorded gas boundary entry and exit positions, not
from the first/last non-zero energy-deposit hits.
"""

import argparse
import csv
import math
import re
from pathlib import Path

import numpy as np
import ROOT

ROOT.gROOT.SetBatch(True)

TRUNCATED_98_GAUSSIAN_STD = 0.934553
GAS_DENSITY_G_CM3 = 0.00665333
GAS_X0_G_CM2 = 1.0 / (0.175 / 94.32 + 0.225 / 42.70 + 0.600 / 34.24)
PARTICLES = {
    "muon": (105.6583755, 1.0),
    "proton": (938.2720882, 1.0),
}


def metadata(path):
    name = path.stem.lower()
    particle = "proton" if "proton" in name else "muon"
    momentum_match = re.search(r"_p([0-9]+(?:\.[0-9]+)?)", name)
    length_match = re.search(r"_l([0-9]+(?:\.[0-9]+)?)", name)
    if not momentum_match or not length_match:
        raise ValueError(f"Cannot parse momentum/length from {path.name}")
    return particle, float(momentum_match.group(1)), float(length_match.group(1))


def central_core_sigma(values, fraction=0.98):
    lo = 0.5 * (1.0 - fraction)
    qlo, qhi = np.quantile(values, [lo, 1.0 - lo])
    kept = values[(values >= qlo) & (values <= qhi)]
    return float(np.std(kept)) / TRUNCATED_98_GAUSSIAN_STD, len(kept)


def pdg_theta0(momentum_mev, mass_mev, length_cm, charge=1.0):
    beta = momentum_mev / math.sqrt(momentum_mev**2 + mass_mev**2)
    x_over_x0 = length_cm * GAS_DENSITY_G_CM3 / GAS_X0_G_CM2
    correction = 1.0 + 0.038 * math.log(x_over_x0 * charge**2 / beta**2)
    theta0 = (
        13.6 / (beta * momentum_mev)
        * charge
        * math.sqrt(x_over_x0)
        * correction
    )
    return theta0, beta, x_over_x0


def load_exit(path):
    root_file = ROOT.TFile.Open(str(path))
    if not root_file or root_file.IsZombie():
        raise OSError(f"Cannot open {path}")
    tree = root_file.Get("Exit")
    if not tree:
        raise KeyError(f"No Exit tree in {path}")
    columns = [branch.GetName() for branch in tree.GetListOfBranches()]
    required = [
        "Event_no", "KE",
        "exit_momentum_x", "exit_momentum_y", "exit_momentum_z",
        "exit_pos_x", "exit_pos_y", "exit_pos_z",
        "entry_KE", "entry_momentum_x", "entry_momentum_y", "entry_momentum_z",
        "entry_pos_x", "entry_pos_y", "entry_pos_z",
        "gas_track_length", "gas_step_count", "entered",
    ]
    missing = sorted(set(required) - set(columns))
    if missing:
        raise KeyError(f"{path.name} lacks new entry/exit branches: {missing}")
    arrays = ROOT.RDataFrame(tree).AsNumpy(required)
    return root_file, {key: np.asarray(value) for key, value in arrays.items()}


def analyze_file(path):
    particle, momentum, length_cm = metadata(path)
    mass, charge = PARTICLES[particle]
    root_file, a = load_exit(path)
    expected_exit_z = 5.0 * length_cm  # cm -> half-length in mm
    downstream = np.isclose(a["exit_pos_z"], expected_exit_z, atol=1.0e-6)
    entered = a["entered"] == 1
    mask = downstream & entered

    theta0, beta, x_over_x0 = pdg_theta0(momentum, mass, length_cm, charge)
    rows = []
    for coordinate in ("x", "y"):
        theta = np.arctan2(
            a[f"exit_momentum_{coordinate}"][mask],
            a["exit_momentum_z"][mask],
        )
        psi = np.arctan2(
            a[f"exit_pos_{coordinate}"][mask]
            - a[f"entry_pos_{coordinate}"][mask],
            a["exit_pos_z"][mask] - a["entry_pos_z"][mask],
        )
        theta_core, n98 = central_core_sigma(theta)
        psi_core, _ = central_core_sigma(psi)
        rows.append({
            "file": path.name,
            "particle": particle,
            "momentum_MeV_c": momentum,
            "length_cm": length_cm,
            "lateral_displacement": "no" if "nolateral" in path.stem.lower() else "yes",
            "projection": coordinate,
            "n_exit": len(a["Event_no"]),
            "n_downstream": int(mask.sum()),
            "n_central98": n98,
            "entry_z_mean_mm": float(np.mean(a["entry_pos_z"][mask])),
            "exit_z_mean_mm": float(np.mean(a["exit_pos_z"][mask])),
            "gas_track_length_mean_mm": float(np.mean(a["gas_track_length"][mask])),
            "gas_step_count_mean": float(np.mean(a["gas_step_count"][mask])),
            "entry_KE_mean_MeV": float(np.mean(a["entry_KE"][mask])),
            "exit_KE_mean_MeV": float(np.mean(a["KE"][mask])),
            "fractional_KE_loss": float(
                np.mean((a["entry_KE"][mask] - a["KE"][mask]) / a["entry_KE"][mask])
            ),
            "beta": beta,
            "x_over_X0": x_over_x0,
            "theta_full_rms_deg": math.degrees(float(np.std(theta))),
            "psi_full_rms_deg": math.degrees(float(np.std(psi))),
            "theta_over_psi_full_rms": float(np.std(theta) / np.std(psi)),
            "theta_core_sigma_deg": math.degrees(theta_core),
            "psi_core_sigma_deg": math.degrees(psi_core),
            "theta_over_psi_core": theta_core / psi_core,
            "pdg_theta0_deg": math.degrees(theta0),
            "theta_core_over_pdg": theta_core / theta0,
        })
    return root_file, rows


def diagnostic_summary(root_file):
    tree = root_file.Get("StepDebug")
    if not tree or tree.GetEntries() == 0:
        return {}
    columns = [branch.GetName() for branch in tree.GetListOfBranches()]
    a = ROOT.RDataFrame(tree).AsNumpy(columns)
    a = {key: np.asarray(value) for key, value in a.items()}
    entry = (a["pre_volume_code"] == 0) & (a["post_volume_code"] == 1)
    gas = a["pre_volume_code"] == 1
    dtheta = np.hypot(
        np.arctan2(a["post_px"], a["post_pz"])
        - np.arctan2(a["pre_px"], a["pre_pz"]),
        np.arctan2(a["post_py"], a["post_pz"])
        - np.arctan2(a["pre_py"], a["pre_pz"]),
    )
    first_gas_indices = []
    for event_id in np.unique(a["Event_no"]):
        indices = np.where(gas & (a["Event_no"] == event_id))[0]
        if len(indices):
            first_gas_indices.append(indices[np.argmin(a["Step_no"][indices])])
    first = np.asarray(first_gas_indices, dtype=int)
    return {
        "debug_events": int(len(np.unique(a["Event_no"]))),
        "entry_post_z_mean_mm": float(np.mean(a["post_z"][entry])),
        "entry_direction_change_max_deg": math.degrees(float(np.max(dtheta[entry]))),
        "first_gas_step_pre_z_mean_mm": float(np.mean(a["pre_z"][first])),
        "first_gas_step_post_z_mean_mm": float(np.mean(a["post_z"][first])),
        "first_gas_step_direction_change_mean_deg": math.degrees(float(np.mean(dtheta[first]))),
        "first_gas_step_direction_change_min_deg": math.degrees(float(np.min(dtheta[first]))),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("entry_exit_scan_output"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_rows = []
    diagnostics = []
    for path in args.files:
        root_file, rows = analyze_file(path)
        all_rows.extend(rows)
        summary = diagnostic_summary(root_file)
        if summary:
            diagnostics.append({"file": path.name, **summary})

    csv_path = args.output_dir / "entry_exit_scan.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)

    diagnostic_path = args.output_dir / "boundary_diagnostic.csv"
    if diagnostics:
        with diagnostic_path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=diagnostics[0].keys())
            writer.writeheader()
            writer.writerows(diagnostics)

    print(f"Wrote {csv_path}")
    if diagnostics:
        print(f"Wrote {diagnostic_path}")
    for row in all_rows:
        print(
            f"{row['length_cm']:5.0f} cm lateral={row['lateral_displacement']:3s} "
            f"{row['projection']}: theta={row['theta_core_sigma_deg']:.5f} deg, "
            f"psi={row['psi_core_sigma_deg']:.5f} deg, "
            f"theta/psi RMS={row['theta_over_psi_full_rms']:.4f}, "
            f"core={row['theta_over_psi_core']:.4f}, "
            f"theta/PDG={row['theta_core_over_pdg']:.4f}, "
            f"dKE/KE={100*row['fractional_KE_loss']:.3f}%"
        )
    for row in diagnostics:
        print("Diagnostic:", row)


if __name__ == "__main__":
    main()
