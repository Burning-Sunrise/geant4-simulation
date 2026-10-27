#!/usr/bin/env python3
"""Compare Sola's original and corrected source coordinates for psi_x."""

import math
from pathlib import Path

import numpy as np
import ROOT


INPUT = Path("/Users/s.x./Downloads/Muon_z.root")
OUTPUT_BASE = Path("/Users/s.x./Desktop/geant4_project/psi_x_wrong_vs_correct")


def central98_sigma(values):
    lo, hi = np.quantile(values, [0.01, 0.99])
    central = values[(values >= lo) & (values <= hi)]
    return np.std(central) / 0.934553


ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetTitleFont(42, "XYZ")
ROOT.gStyle.SetLabelFont(42, "XYZ")
ROOT.gStyle.SetLegendFont(42)

root_file = ROOT.TFile.Open(str(INPUT))
gas = root_file.Get("Gas")
arrays = ROOT.RDataFrame(gas).AsNumpy(["Event_no", "x", "z"])
event = np.asarray(arrays["Event_no"])
x = np.asarray(arrays["x"])
z = np.asarray(arrays["z"])

# Reproduce df_hits.groupby("Event_no").agg(list) followed by v[-1].
# np.unique on the reversed event array returns the final tree row for each event.
_, reverse_first = np.unique(event[::-1], return_index=True)
last = len(event) - 1 - reverse_first
x_last = x[last]
z_last = z[last]

# After Sola's rotation, x' = z and y' = x.  Thus her phi_hit is the
# signed projected x angle atan2(x_last, z_last - source_x').
psi_wrong = np.degrees(np.arctan2(x_last, z_last + 50.0))
psi_correct = np.degrees(np.arctan2(x_last, z_last + 500.0))

finite = np.isfinite(psi_wrong) & np.isfinite(psi_correct)
psi_wrong = psi_wrong[finite]
psi_correct = psi_correct[finite]

hist_wrong = ROOT.TH1D("hist_wrong", "", 150, -15.0, 15.0)
hist_correct = ROOT.TH1D("hist_correct", "", 150, -15.0, 15.0)
hist_wrong.Sumw2()
hist_correct.Sumw2()
for value in psi_wrong:
    hist_wrong.Fill(float(value))
for value in psi_correct:
    hist_correct.Fill(float(value))

hist_wrong.Scale(1.0 / hist_wrong.Integral("width"))
hist_correct.Scale(1.0 / hist_correct.Integral("width"))

canvas = ROOT.TCanvas("canvas", "psi source comparison", 1200, 760)
canvas.SetLeftMargin(0.12)
canvas.SetRightMargin(0.04)
canvas.SetBottomMargin(0.13)
canvas.SetTopMargin(0.09)

hist_wrong.SetLineColor(ROOT.kRed + 1)
hist_wrong.SetLineWidth(3)
hist_correct.SetLineColor(ROOT.kBlue + 1)
hist_correct.SetLineWidth(3)
hist_wrong.GetXaxis().SetTitle("#psi_{x} [deg]")
hist_wrong.GetYaxis().SetTitle("Normalized entries / degree")
hist_wrong.GetXaxis().SetTitleSize(0.052)
hist_wrong.GetYaxis().SetTitleSize(0.052)
hist_wrong.GetXaxis().SetLabelSize(0.043)
hist_wrong.GetYaxis().SetLabelSize(0.043)
hist_wrong.GetYaxis().SetTitleOffset(1.08)
hist_wrong.SetMaximum(1.18 * max(hist_wrong.GetMaximum(), hist_correct.GetMaximum()))
hist_wrong.Draw("HIST")
hist_correct.Draw("HIST SAME")

wrong_rms = float(np.std(psi_wrong))
correct_rms = float(np.std(psi_correct))
wrong_core = float(central98_sigma(psi_wrong))
correct_core = float(central98_sigma(psi_correct))

legend = ROOT.TLegend(0.57, 0.67, 0.92, 0.84)
legend.SetBorderSize(0)
legend.SetFillStyle(0)
legend.SetTextSize(0.039)
legend.AddEntry(
    hist_wrong,
    f"Original -50: #sigma_{{core}} = {wrong_core:.2f} deg",
    "l",
)
legend.AddEntry(
    hist_correct,
    f"Correct -500 mm: #sigma_{{core}} = {correct_core:.2f} deg",
    "l",
)
legend.Draw()

latex = ROOT.TLatex()
latex.SetNDC(True)
latex.SetTextFont(42)
latex.SetTextSize(0.052)
title = ROOT.TLatex()
title.SetNDC(True)
title.SetTextFont(42)
title.SetTextSize(0.050)
title.DrawLatex(0.12, 0.925, "Effect of the entrance-coordinate unit on #psi_{x}")
latex.SetTextSize(0.034)
latex.DrawLatex(0.15, 0.83, "Muon_z.root; last non-zero-energy Gas hit")
latex.DrawLatex(0.15, 0.78, "ROOT coordinates: GasBox boundaries at z = #pm500 mm")

canvas.RedrawAxis()
canvas.SaveAs(str(OUTPUT_BASE.with_suffix(".png")))
canvas.SaveAs(str(OUTPUT_BASE.with_suffix(".pdf")))

print(f"events = {len(psi_wrong)}")
print(f"wrong source -50: full RMS = {wrong_rms:.6f} deg, central98 sigma = {wrong_core:.6f} deg")
print(f"correct source -500 mm: full RMS = {correct_rms:.6f} deg, central98 sigma = {correct_core:.6f} deg")
print(f"RMS width ratio wrong/correct = {wrong_rms/correct_rms:.6f}")
print(f"wrote {OUTPUT_BASE.with_suffix('.png')}")
print(f"wrote {OUTPUT_BASE.with_suffix('.pdf')}")
