# Screen grab

Python scripts that turn a folder of lab run workbooks into report-ready table images, in one run.

I wrote them in 2023 for a validation study of two reporter-gene assays used to detect endocrine disruptors. Each experiment produced one Excel workbook per run, and the study report needed the same key values from every run, laid out the same way. Instead of copying cells and taking screenshots by hand, the script opens every workbook in a folder, reads the right cells and exports one PNG per chemical.

**Live case study with an interactive walkthrough:** https://luminou.github.io/Screen_grab/
**All data projects:** https://luminou.github.io/Data_Projects/

> The study workbooks are not public. The web page uses invented example values and a sheet layout rebuilt from the cell addresses in the scripts.

---

## The assays

- **GRTA**: glucocorticoid receptor transactivation. The receptor for cortisol (stress, inflammation, metabolism).
- **RARTA**: retinoic acid receptor transactivation. The receptor for retinoic acid, made from vitamin A (development, differentiation).
- **AGO**: the chemical alone; light in % of the reference agonist's maximum.
- **ANT**: the chemical with the reference agonist at ~80 % (Ref80); a drop means the receptor is blocked.
- **INT**: the chemical with the reference at 100 %; separates true competition from interference with the cells or the light reaction.
- **Viability**: read for every dose, so a drop in light only counts if the cells are alive.

Each plate holds two chemicals (top rows A–D, bottom rows E–H), each at 7 concentrations in 4 replicate wells.

## What the script does

For every `*.xlsx` (GRTA) or `*.xlsm` (RARTA) file in the input folder:

1. Read the run identity and plate controls from fixed cells of the `Luminescence` sheet.
2. Read two 7-row data blocks (top and bottom chemical of the plate) from the `Luminescence` and `Viability` sheets: concentration, four normalised replicates, mean, SD and CV.
3. Build three tables with Bokeh `DataTable` (identity, luminescence, viability) and lay them out in a grid.
4. Export the grid as `Molecule_Mode_Run_Date.png` with `bokeh.io.export_png`.
5. Repeat for the bottom chemical, unless the cell reads `no compound`.

## Cells read

| Field | Cell | pandas call |
|---|---|---|
| Date | E4 | `df.iat[2, 4]` |
| Co-exposure concentration of the reference agonist (ANT, INT) | E11 | `df.iat[9, 4]` |
| Top chemical / mode / run | E15 / G15 / H15 | `df.iat[13, 4]`, `df.iat[13, 6]`, `df.iat[13, 7]` |
| Bottom chemical / run | E16 / H16 | `df.iat[14, 4]`, `df.iat[14, 7]` |
| Basal (% mean, % sd) | E19:F19 | `df.iat[17, 4]`, `df.iat[17, 5]` |
| Induction factor (mean, sd) | E20:F20 | `df.iat[18, 4]`, `df.iat[18, 5]` |
| Ref80 (% mean, % sd), ANT only | E21:F21 | `df.iat[19, 4]`, `df.iat[19, 5]` |
| Top data block | rows 31–37, columns D, L:O, P, Q, S | `read_excel(skiprows=29, nrows=7, usecols='D,L:O, P, Q, S')` |
| Bottom data block | rows 43–49, same columns | `read_excel(skiprows=41, nrows=7, ...)` |

## The six variants

| Script | Assay | Mode | Extra fields |
|---|---|---|---|
| `..._GRTA_..._AGO.py` | Glucocorticoid receptor transactivation (phase 2, `.xlsx`) | Agonist | none |
| `..._GRTA_..._ANT.py` | Glucocorticoid receptor transactivation | Antagonist | Ref80, co-exposure concentration |
| `..._GRTA_..._INT.py` | Glucocorticoid receptor transactivation | Interference | co-exposure concentration |
| `..._RARTA_..._AGO.py` | Retinoic acid receptor transactivation (phase 1, `.xlsm`) | Agonist | none |
| `..._RARTA_..._ANT.py` | Retinoic acid receptor transactivation | Antagonist | Ref80, co-exposure concentration |
| `..._RARTA_..._INT.py` | Retinoic acid receptor transactivation | Interference | co-exposure concentration |

## Running it

Requirements: Python 3, pandas, openpyxl, Bokeh, and for PNG export Selenium with a browser driver.

```bash
conda install pandas openpyxl bokeh
conda install selenium geckodriver firefox -c conda-forge
```

Set the two folder paths at the top of the script (`os.chdir(...)` and `mydir = Path(...)`), then run it. The PNG files are written to that folder.

## Known limits and what I would change today

- Bokeh is built for interactive pages, so exporting static PNGs through a headless browser is slow. A matplotlib table, or HTML/PDF output, would be faster.
- `set_axis(..., inplace=True)` is deprecated in recent pandas versions.
- Ref80 for antagonist runs and Ref100 for interference runs were still to be added in some variants.
- The six scripts differ only in a folder, a file extension and a few cell addresses. One script driven by a small configuration table would replace them:

```python
LAYOUT = {
    'AGO': dict(extra={}),
    'ANT': dict(extra={'Ref80': 'E21:F21', 'Coexpo': 'E11'}),
    'INT': dict(extra={'Coexpo': 'E11'}),
}
for assay, ext in [('GRTA', 'xlsx'), ('RARTA', 'xlsm')]:
    for mode, cfg in LAYOUT.items():
        for wb in (ROOT / assay / mode).glob(f'*.{ext}'):
            export_card(read_run(wb, cfg))
```

## Author

Clémentine Garoche
