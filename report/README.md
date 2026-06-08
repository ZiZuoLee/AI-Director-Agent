# Project Report (English PDF)

This report uses the official [ICLR Master-Template](https://github.com/ICLR/Master-Template) (ICLR 2025 style files).

## Files

| File | Source |
|------|--------|
| `iclr2025_conference.sty` | ICLR Master-Template / `iclr2025/` |
| `iclr2025_conference.bst` | ICLR Master-Template / `iclr2025/` |
| `fancyhdr.sty`, `natbib.sty` | ICLR Master-Template / `iclr2025/` |
| `math_commands.tex` | ICLR Master-Template / `iclr2025/` |
| `main.tex` | Project report content |
| `references.bib` | Bibliography (public APIs and libraries) |

## Build PDF

Requires a LaTeX distribution (TeX Live / MiKTeX).

```powershell
cd report
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Output: `main.pdf`

## Before submission

1. Replace `TBD` student IDs in the Team Contributions table (`main.tex`).
2. Optionally add result screenshots under `figures/` and include with `\includegraphics`.
3. Verify the repository URL in the abstract.
