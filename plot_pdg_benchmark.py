#!/usr/bin/env python3
"""Make a compact meeting-ready comparison from the benchmark CSV files."""

import csv
from pathlib import Path
from statistics import mean

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

BASE = Path(__file__).resolve().parent / "pdg_benchmark_output"


def averages(path):
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    result = {}
    for particle in ("muon", "proton"):
        selected = [row for row in rows if row["particle"] == particle]
        result[particle] = {
            "geant_over_pdg": mean(float(row["geant_over_pdg"]) for row in selected),
            "ratio_over_sqrt3": mean(float(row["ratio_over_sqrt3"]) for row in selected),
        }
    return result


def graph(values, color, marker):
    result = ROOT.TGraph(2)
    for index, value in enumerate(values, 1):
        result.SetPoint(index - 1, index, value)
    result.SetMarkerColor(color)
    result.SetLineColor(color)
    result.SetMarkerStyle(marker)
    result.SetMarkerSize(1.5)
    result.SetLineWidth(2)
    return result


def draw_panel(pad, title, y_title, original_values, emy_values, ymin, ymax):
    pad.cd()
    pad.SetGridy()
    frame = ROOT.TH1D(f"frame_{pad.GetName()}", f"{title};particle;{y_title}", 2, 0.5, 2.5)
    frame.SetMinimum(ymin)
    frame.SetMaximum(ymax)
    frame.GetXaxis().SetBinLabel(1, "#mu^{-}, 1 GeV/c")
    frame.GetXaxis().SetBinLabel(2, "p, 5 GeV/c")
    frame.GetYaxis().SetTitleOffset(1.25)
    frame.Draw("axis")
    unity = ROOT.TLine(0.5, 1.0, 2.5, 1.0)
    unity.SetLineStyle(ROOT.kDashed)
    unity.SetLineWidth(2)
    unity.Draw()
    original = graph(original_values, ROOT.kBlue + 1, 20)
    emy = graph(emy_values, ROOT.kRed + 1, 21)
    original.Draw("LP same")
    emy.Draw("LP same")
    legend = ROOT.TLegend(0.15, 0.75, 0.47, 0.89)
    legend.SetBorderSize(0)
    legend.AddEntry(original, "FTFP_BERT", "lp")
    legend.AddEntry(emy, "FTFP_BERT_EMY", "lp")
    legend.Draw()
    return frame, unity, original, emy, legend


def main():
    original = averages(BASE / "summary_original.csv")
    emy = averages(BASE / "summary.csv")
    particles = ("muon", "proton")
    canvas = ROOT.TCanvas("c", "PDG benchmark", 1100, 480)
    canvas.Divide(2, 1)
    keepalive = []
    keepalive.extend(draw_panel(
        canvas.cd(1), "Projected angular width", "Geant4 #sigma_{#theta} / PDG #theta_{0}",
        [original[p]["geant_over_pdg"] for p in particles],
        [emy[p]["geant_over_pdg"] for p in particles], 0.98, 1.07))
    keepalive.extend(draw_panel(
        canvas.cd(2), "Endpoint-displacement relation", "(#sigma_{#theta}/#sigma_{#psi}) / #sqrt{3}",
        [original[p]["ratio_over_sqrt3"] for p in particles],
        [emy[p]["ratio_over_sqrt3"] for p in particles], 0.98, 1.04))
    canvas.SaveAs(str(BASE / "pdg_benchmark_comparison.png"))


if __name__ == "__main__":
    main()
