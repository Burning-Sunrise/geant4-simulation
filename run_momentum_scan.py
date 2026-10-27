#!/usr/bin/env python3
"""Run a Geant4 muon momentum scan with exact gas entry/exit recording."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


MOMENTA_MEV_C = [50, 75, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000]


def macro_text(momentum: int, events: int, output_file: Path, threads: int) -> str:
    seed1 = 17389 + 97 * momentum
    seed2 = 29021 + 193 * momentum
    return f"""/control/verbose 0
/run/verbose 0
/event/verbose 0
/tracking/verbose 0
/run/numberOfThreads {threads}
/B1/det/gasLength 100 cm
/process/msc/MuHadLateralDisplacement true
/run/initialize
/analysis/setFileName {output_file}
/gun/particle mu-
/gun/momentumAmp {momentum} MeV
/gun/position 0 0 -51 cm
/gun/direction 0 0 1
/run/printProgress 5000
/random/setSeeds {seed1} {seed2}
/run/beamOn {events}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=30000)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--scan-label",
        default="momentum_scan",
        help="Output directory name under the project directory.",
    )
    args = parser.parse_args()

    project = Path(__file__).resolve().parent
    b1 = project / "B1_copy"
    binary = b1 / "build_pixi_validation" / "exampleB1"
    scan_dir = project / args.scan_label
    macro_dir = scan_dir / "macros"
    root_dir = scan_dir / "root"
    log_dir = scan_dir / "logs"
    for directory in (macro_dir, root_dir, log_dir):
        directory.mkdir(parents=True, exist_ok=True)

    for momentum in MOMENTA_MEV_C:
        root_file = root_dir / f"muon_p{momentum}_L100_true_boundaries.root"
        macro_file = macro_dir / f"muon_p{momentum}_L100.mac"
        log_file = log_dir / f"muon_p{momentum}_L100.log"
        macro_file.write_text(
            macro_text(momentum, args.events, root_file, args.threads),
            encoding="utf-8",
        )

        if root_file.exists() and not args.force:
            print(f"Skipping existing {root_file.name}")
            continue

        print(f"Running p = {momentum} MeV/c ({args.events:,} events)")
        with log_file.open("w", encoding="utf-8") as log:
            subprocess.run(
                ["pixi", "run", str(binary), str(macro_file)],
                cwd=project,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )


if __name__ == "__main__":
    main()
