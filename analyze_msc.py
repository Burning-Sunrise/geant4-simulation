#!/usr/bin/env python3
"""Analyze Geant4 exit records without requiring uproot.

The script deliberately keeps three observables separate:
  theta_u: final projected direction angle in transverse plane u;
  psi_u:   projected endpoint displacement angle atan(delta_u / delta_long);
  theta_3d: non-projected space angle between initial and final directions.

PDG theta_0 is the width of ONE projected final-angle distribution.  The
often-quoted psi_rms = theta_0/sqrt(3) is an endpoint-displacement result for
constant scattering power, not a conversion between arbitrary angle fits.
"""

import argparse
import csv
import math
from pathlib import Path

import numpy as np
import ROOT

ROOT.gROOT.SetBatch(True)

# DetectorConstruction.cc: He:CO2 = 70:30 molar at 10 atm and 293.15 K.
# Radiation lengths are mass radiation lengths in g/cm^2.
GAS_DENSITY_G_CM3 = 0.00665333
GAS_X0_G_CM2 = 1.0 / (0.175 / 94.32 + 0.225 / 42.70 + 0.600 / 34.24)
X_OVER_X0 = 100.0 * GAS_DENSITY_G_CM3 / GAS_X0_G_CM2
TRUNCATED_98_GAUSSIAN_STD = 0.934553


def beam_metadata(path):
    name = path.stem.lower()
    if "mu" in name:
        mass, particle = 105.6583755, "muon"
    elif "proton" in name:
        mass, particle = 938.2720882, "proton"
    else:
        return None
    import re
    match = re.search(r"_p([0-9]+(?:\.[0-9]+)?)", name)
    if not match:
        return None
    momentum = float(match.group(1))
    beta = momentum / math.sqrt(momentum * momentum + mass * mass)
    correction = 1.0 + 0.038 * math.log(X_OVER_X0)
    theta0 = 13.6 / (beta * momentum) * math.sqrt(X_OVER_X0) * correction
    return particle, momentum, math.degrees(theta0)


def central_rms(values, fraction=0.98):
    """RMS about the retained sample mean after symmetric quantile trimming."""
    lo = (1.0 - fraction) / 2.0
    qlo, qhi = np.quantile(values, [lo, 1.0 - lo])
    kept = values[(values >= qlo) & (values <= qhi)]
    return float(np.std(kept)), len(kept)


def infer_axis(path):
    name = path.stem.lower()
    if "_x" in name:
        return "x"
    if "_z" in name:
        return "z"
    raise ValueError(f"Cannot infer beam axis from {path.name}; pass --axis")


def load_exit(path):
    root_file = ROOT.TFile.Open(str(path))
    if not root_file or root_file.IsZombie():
        raise OSError(f"Cannot open {path}")
    tree = root_file.Get("Exit")
    if not tree:
        raise KeyError(f"No Exit tree in {path}")
    arrays = ROOT.RDataFrame(tree).AsNumpy()
    return {key: np.asarray(value) for key, value in arrays.items()}


def analyze(path, axis):
    a = load_exit(path)
    transverse = ("y", "z") if axis == "x" else ("x", "y")
    p_long = a[f"exit_momentum_{axis}"]
    pos_long = a[f"exit_pos_{axis}"]
    # All supplied/validation macros start 10 mm outside the -500 mm gas face.
    delta_long = pos_long - (-510.0)
    rows = []
    metadata = beam_metadata(path)
    projected = {}
    for coordinate in transverse:
        theta = np.arctan2(a[f"exit_momentum_{coordinate}"], p_long)
        psi = np.arctan2(a[f"exit_pos_{coordinate}"], delta_long)
        theta98, n98 = central_rms(theta)
        psi98, _ = central_rms(psi)
        projected[coordinate] = (theta, psi)
        core_sigma = theta98 / TRUNCATED_98_GAUSSIAN_STD
        pdg_theta = metadata[2] if metadata else float("nan")
        rows.append({
            "file": path.name,
            "beam_axis": axis,
            "projection": coordinate,
            "n_exit": len(theta),
            "mean_exit_ke_MeV": float(np.mean(a["KE"])),
            "theta_rms_deg": math.degrees(float(np.std(theta))),
            "psi_rms_deg": math.degrees(float(np.std(psi))),
            "theta_over_psi": float(np.std(theta) / np.std(psi)),
            "theta_central98_rms_deg": math.degrees(theta98),
            "theta_core_sigma_deg": math.degrees(core_sigma),
            "pdg_theta0_deg": pdg_theta,
            "core_over_pdg": math.degrees(core_sigma) / pdg_theta,
            "psi_central98_rms_deg": math.degrees(psi98),
            "central98_theta_over_psi": theta98 / psi98,
            "corr_theta_psi": float(np.corrcoef(theta, psi)[0, 1]),
            "n_central98": n98,
        })
    p2 = sum(a[f"exit_momentum_{q}"] ** 2 for q in ("x", "y", "z"))
    theta3d = np.arccos(np.clip(p_long / np.sqrt(p2), -1.0, 1.0))
    return rows, projected, theta3d


def make_plot(all_results, output):
    count = len(all_results)
    columns = 2 if count <= 4 else 3
    rows = math.ceil(count / columns)
    canvas = ROOT.TCanvas("c", "Projected multiple scattering", 600 * columns, 400 * rows)
    canvas.Divide(columns, rows)
    colors = [ROOT.kBlue + 1, ROOT.kRed + 1, ROOT.kGreen + 2, ROOT.kMagenta + 1]
    keepalive = []
    for pad_index, (label, (projected, _theta3d)) in enumerate(all_results.items(), 1):
        canvas.cd(pad_index)
        ROOT.gPad.SetGrid()
        coord = next(iter(projected))
        theta, psi = projected[coord]
        # Show the Gaussian core addressed by the PDG approximation; rare
        # proton nuclear-scattering tails otherwise flatten the useful region.
        limit = float(np.quantile(np.abs(np.concatenate([theta, psi])), 0.98))
        hist_theta = ROOT.TH1D(f"ht{pad_index}", f"{label};angle [deg];normalized entries", 90,
                               -math.degrees(limit), math.degrees(limit))
        hist_psi = ROOT.TH1D(f"hp{pad_index}", "", 90,
                             -math.degrees(limit), math.degrees(limit))
        for value in np.degrees(theta):
            hist_theta.Fill(float(value))
        for value in np.degrees(psi):
            hist_psi.Fill(float(value))
        for hist, color in ((hist_theta, colors[0]), (hist_psi, colors[1])):
            if hist.Integral():
                hist.Scale(1.0 / hist.Integral())
            hist.SetLineColor(color)
            hist.SetLineWidth(2)
        hist_theta.SetMaximum(1.18 * max(hist_theta.GetMaximum(), hist_psi.GetMaximum()))
        hist_theta.Draw("hist")
        hist_psi.Draw("hist same")
        legend = ROOT.TLegend(0.57, 0.72, 0.88, 0.88)
        legend.AddEntry(hist_theta, "exit direction #theta", "l")
        legend.AddEntry(hist_psi, "endpoint angle #psi", "l")
        legend.Draw()
        hist_theta.SetStats(False)
        hist_psi.SetStats(False)
        keepalive.extend((hist_theta, hist_psi, legend))
    canvas.cd(0)
    canvas.Modified()
    canvas.Update()
    canvas.SaveAs(str(output))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--axis", choices=("x", "z"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis_output"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    all_results = {}
    for path in args.files:
        axis = args.axis or infer_axis(path)
        result_rows, projected, theta3d = analyze(path, axis)
        rows.extend(result_rows)
        all_results[path.stem] = (projected, theta3d)
    csv_path = args.output_dir / "msc_summary.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    plot_path = args.output_dir / "projected_angle_distributions.png"
    make_plot(all_results, plot_path)
    print(f"Wrote {csv_path}")
    print(f"Wrote {plot_path}")
    for row in rows:
        print(f"{row['file']:35s} {row['projection']}: "
              f"theta/psi={row['theta_over_psi']:.3f}, "
              f"central98={row['central98_theta_over_psi']:.3f}, "
              f"core/PDG={row['core_over_pdg']:.3f}, "
              f"core_sigma={row['theta_core_sigma_deg']:.3f} deg")


if __name__ == "__main__":
    main()
