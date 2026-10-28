"""
Screen grab: turn a folder of run workbooks into report-ready table images.

Every run workbook follows the same template: a `Luminescence` sheet holding the
run identity, the plate controls and two 7-row data blocks (top and bottom
chemical of the plate), and a `Viability` sheet with the same data blocks.
For each chemical, the script reads those fixed cells and saves one PNG with
three tables: identity, luminescence and viability.

Folder layout expected under ROOT:
    ROOT/GRTA/AGO/*.xlsx   ROOT/GRTA/ANT/*.xlsx   ROOT/GRTA/INT/*.xlsx
    ROOT/RARTA/AGO/*.xlsm  ROOT/RARTA/ANT/*.xlsm  ROOT/RARTA/INT/*.xlsm

Usage:
    python screen_grab.py ROOT [--out OUTPUT_FOLDER]
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

# What changes between modes: the extra cells read for the identity table.
LAYOUT = {
    'AGO': dict(extra={}),
    'ANT': dict(extra={'Ref80': 'E21:F21', 'Coexpo': 'E11'}),
    'INT': dict(extra={'Coexpo': 'E11'}),
}
ASSAYS = [('GRTA', 'xlsx'), ('RARTA', 'xlsm')]

# Cells shared by every run (Excel addresses on the Luminescence sheet).
COMMON = {'Date': 'E4', 'Mode': 'G15', 'Basal': 'E19:F19', 'IF': 'E20:F20'}
HALVES = {  # chemical name, run number, first data row
    'top': dict(molecule='E15', run='H15', first_row=31),
    'bottom': dict(molecule='E16', run='H16', first_row=43),
}
BLOCK_COLS = ['D', 'L', 'M', 'N', 'O', 'P', 'Q', 'S']
BLOCK_NAMES = ['Conc (M)', 'norm1', 'norm2', 'norm3', 'norm4', 'mean %', 'sd %', 'CV %']
N_DOSES = 7


def col_index(letters):
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def cell(sheet, address):
    """Value of one Excel cell ('E4') in a sheet read with header=None."""
    letters = ''.join(c for c in address if c.isalpha())
    row = int(''.join(c for c in address if c.isdigit())) - 1
    return sheet.iat[row, col_index(letters)]


def cells(sheet, address):
    """One cell ('E11') or a horizontal pair ('E21:F21') -> value or (value, value)."""
    if ':' in address:
        a, b = address.split(':')
        return cell(sheet, a), cell(sheet, b)
    return cell(sheet, address)


def block(sheet, first_row):
    """The 7 x 8 data block starting at Excel row `first_row`."""
    rows = []
    for r in range(first_row, first_row + N_DOSES):
        rows.append([cell(sheet, f'{c}{r}') for c in BLOCK_COLS])
    return pd.DataFrame(rows, columns=BLOCK_NAMES)


def read_run(wb, cfg):
    """Read one workbook; return one record per chemical present on the plate."""
    lum = pd.read_excel(wb, sheet_name='Luminescence', header=None)
    via = pd.read_excel(wb, sheet_name='Viability', header=None)
    shared = {k: cells(lum, a) for k, a in COMMON.items()}
    shared.update({k: cells(lum, a) for k, a in cfg['extra'].items()})
    records = []
    for half, pos in HALVES.items():
        molecule = cell(lum, pos['molecule'])
        if not isinstance(molecule, str) or molecule.strip().lower() == 'no compound':
            continue  # empty half of the plate
        records.append(dict(shared, Molecule=molecule, Run=cell(lum, pos['run']), half=half,
                            luminescence=block(lum, pos['first_row']),
                            viability=block(via, pos['first_row'])))
    return records


def fmt_pct(v):
    return '' if pd.isna(v) else f'{float(v):.1%}'


def fmt_sci(v):
    return '' if pd.isna(v) else f'{float(v):.2e}'


def identity_table(rec):
    head = ['Date', 'Molecule', 'Mode', 'Run', 'Basal (%mean)', 'Basal (%sd)',
            'Induction factor (mean)', 'Induction factor (sd)']
    row = [rec['Date'], rec['Molecule'], rec['Mode'], rec['Run'],
           fmt_pct(rec['Basal'][0]), fmt_pct(rec['Basal'][1]),
           f"{float(rec['IF'][0]):.1f}", f"{float(rec['IF'][1]):.1f}"]
    if 'Ref80' in rec:
        head += ['Ref80 (%mean)', 'Ref80 (%sd)']
        row += [fmt_pct(rec['Ref80'][0]), fmt_pct(rec['Ref80'][1])]
    if 'Coexpo' in rec:
        head += ['Conc coexpo (M)']
        row += [fmt_sci(rec['Coexpo'])]
    return head, [[str(x) for x in row]]


def block_rows(df):
    return [[fmt_sci(r.iloc[0])] + [fmt_pct(v) for v in r.iloc[1:]] for _, r in df.iterrows()]


def draw_table(ax, head, rows, title=None):
    ax.axis('off')
    t = ax.table(cellText=rows, colLabels=head, loc='upper center', cellLoc='left')
    t.auto_set_font_size(False)
    t.set_fontsize(8)
    t.auto_set_column_width(list(range(len(head))))
    t.scale(1, 1.3)
    for (r, _), c in t.get_celld().items():
        c.set_edgecolor('#d0d0d0')
        if r == 0:
            c.set_facecolor('#f2f2f2')
            c.set_text_props(weight='bold')
    if title:
        ax.set_title(title, loc='left', fontsize=10, fontweight='bold')


def export_card(records, out_dir):
    """Save one PNG per chemical, named Molecule_Mode_Run_Date.png."""
    saved = []
    for rec in records:
        fig = plt.figure(figsize=(13, 4.2), dpi=150)
        grid = fig.add_gridspec(2, 2, height_ratios=[1, 3.2], hspace=.35, wspace=.06)
        draw_table(fig.add_subplot(grid[0, :]), *identity_table(rec))
        draw_table(fig.add_subplot(grid[1, 0]), BLOCK_NAMES, block_rows(rec['luminescence']), 'Luminescence')
        draw_table(fig.add_subplot(grid[1, 1]), BLOCK_NAMES, block_rows(rec['viability']), 'Viability')
        name = '_'.join(str(x) for x in (rec['Molecule'], rec['Mode'], rec['Run'], rec['Date'])) + '.png'
        path = Path(out_dir) / name
        fig.savefig(path, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        saved.append(path)
    return saved


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('root', type=Path, help='folder containing GRTA/ and RARTA/')
    ap.add_argument('--out', type=Path, help='output folder (default: next to each workbook)')
    args = ap.parse_args()
    ROOT = args.root
    total = 0
    for assay, ext in ASSAYS:
        for mode, cfg in LAYOUT.items():
            for wb in sorted((ROOT / assay / mode).glob(f'*.{ext}')):
                out = args.out or wb.parent
                out.mkdir(parents=True, exist_ok=True)
                saved = export_card(read_run(wb, cfg), out)
                total += len(saved)
                print(f'{wb.name}: {len(saved)} image(s)')
    print(f'Done: {total} image(s).')


if __name__ == '__main__':
    main()
