# Geant4 progress report

Source snapshot downloaded from Overleaf on 24 November 2026.

- Main document: `Geant4_Report_Nov_2026.tex`
- Current Overleaf PDF: `Geant4_Report_Nov_2026.pdf`
- Companion images: `figures/`

Only the current report source and its required figures are included.
The geometry schematic (Figure 1) is drawn directly in the LaTeX source.

Compile from this directory with:

```sh
latexmk -pdf Geant4_Report_Nov_2026.tex
```

Alternatively, run `pdflatex` twice on the main document. This repository is a
snapshot, not an automatic two-way sync with Overleaf. Export the current
Overleaf source again before updating this folder.
