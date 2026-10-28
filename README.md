# Screen grab

A Python script that turns a folder of lab run workbooks into report-ready table images, in one run.

I wrote it in 2023 for a validation study of two reporter-gene assays used to detect endocrine disruptors. Each experiment produced one Excel workbook per run, and the study report needed the same key values from every run, laid out the same way. Instead of copying cells and taking screenshots by hand, `screen_grab.py` opens every workbook, reads the right cells and exports one PNG per chemical.

**Live case study with an interactive walkthrough:** https://luminou.github.io/Screen_grab/
**All data projects:** https://luminou.github.io/Data_Projects/

> The study workbooks are not public. The web page uses invented example values and a sheet layout rebuilt from the cell addresses the script reads.

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

For every workbook in `ROOT/<assay>/<mode>/`:

1. Read the run identity and plate controls from fixed cells of the `Luminescence` sheet, plus the extra cells of that mode.
2. Read two 7-row data blocks (top and bottom chemical of the plate) from the `Luminescence` and `Viability` sheets: concentration, four normalised replicates, mean, SD and CV.
3. Skip the bottom half when its chemical cell reads `no compound`.
4. Draw three matplotlib tables (identity, luminescence, viability) and save them as `Molecule_Mode_Run_Date.png`.

The six assay–mode combinations differ only in a folder, a file extension and a few cell addresses. They are kept in one table, with the extraction written once:

```python
LAYOUT = {
    'AGO': dict(extra={}),
    'ANT': dict(extra={'Ref80': 'E21:F21', 'Coexpo': 'E11'}),
    'INT': dict(extra={'Coexpo': 'E11'}),
}
for assay, ext in [('GRTA', 'xlsx'), ('RARTA', 'xlsm')]:
    for mode, cfg in LAYOUT.items():
        for wb in (ROOT / assay / mode).glob(f'*.{ext}'):
            export_card(read_run(wb, cfg))  # matplotlib table
```

## Cells read

| Field | Cell |
|---|---|
| Date | E4 |
| Co-exposure concentration of the reference agonist (ANT, INT) | E11 |
| Top chemical / mode / run | E15 / G15 / H15 |
| Bottom chemical / run | E16 / H16 |
| Basal (% mean, % sd) | E19:F19 |
| Induction factor (mean, sd) | E20:F20 |
| Ref80 (% mean, % sd), ANT only | E21:F21 |
| Top data block | rows 31–37, columns D, L:O, P, Q, S |
| Bottom data block | rows 43–49, same columns |

## Running it

Requirements: Python 3 with pandas, openpyxl and matplotlib.

```bash
pip install pandas openpyxl matplotlib
python screen_grab.py ROOT --out reports
```

`ROOT` contains `GRTA/AGO`, `GRTA/ANT`, `GRTA/INT`, `RARTA/AGO`, `RARTA/ANT` and `RARTA/INT`. Without `--out`, each image is saved next to its workbook.

## Author

Clémentine Garoche
