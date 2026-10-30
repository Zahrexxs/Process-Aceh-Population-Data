# Aceh Population Data Processing

Processes village-level population data (CSV) into a formatted Excel report. It
aggregates counts to the Kabupaten (district) and Kecamatan (sub-district) levels
and formats region codes.

## Features

- Filters rows by a configurable region-code prefix (default `1103`).
- Aggregates population counts from Desa (village) level to Kecamatan and Kabupaten levels.
- Formats region codes (`1103` → `11.03`, `110301` → `11.03.01`, `1103012001` → `11.03.01.2001`).
- Generates a pivoted Excel report with Male/Female/Total columns.
- Resolves CSV columns by header name, with a positional fallback for the published BPS layout.
- Clear errors when the input file or expected columns are missing.

## Requirements

- Python 3.10+
- `pandas`, `openpyxl`

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

Place the BPS CSV in the repository root (default filename
`jumlah-penduduk-desa-berdasarkan-jenis-kelamin.csv`) and run:

```bash
python process_population.py
```

Or pass paths and the region prefix explicitly:

```bash
python process_population.py \
  --input data/jumlah-penduduk-desa-berdasarkan-jenis-kelamin.csv \
  --output output/Population_Data_Processed.xlsx \
  --prefix 1105
```

| Option | Default | Description |
|---|---|---|
| `-i`, `--input` | `jumlah-penduduk-desa-berdasarkan-jenis-kelamin.csv` | Input CSV path |
| `-o`, `--output` | `Population_Data_Processed.xlsx` | Output Excel path |
| `-p`, `--prefix` | `1103` | Desa code prefix (Kabupaten/City) to keep |
| `--sep` | `;` | CSV delimiter |

## Output

An Excel file with one sheet and the columns:

| Column | Description |
|---|---|
| `KODE` | Formatted region code (kabupaten, kecamatan, or desa) |
| `DESA` | Region name (level matches the code) |
| `LAKI-LAKI` | Male population |
| `PEREMPUAN` | Female population |
| `TOTAL` | `LAKI-LAKI` + `PEREMPUAN` |

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## License

No license file is included in this repository. All rights reserved.
