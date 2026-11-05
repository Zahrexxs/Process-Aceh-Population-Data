<div align="center">

# Aceh Population Data Processing

**Turn messy BPS village-level CSV exports into a clean, layered Excel report.**

[![CI](https://github.com/Zahrexxs/Process-Aceh-Population-Data/actions/workflows/ci.yml/badge.svg)](https://github.com/Zahrexxs/Process-Aceh-Population-Data/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)
![openpyxl](https://img.shields.io/badge/openpyxl-3.x-217346?logo=microsoftexcel&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)

Aggregates village population data to **Kabupaten**, **Kecamatan** and **Desa**
level, pivots male/female counts, and formats Indonesian region codes.

</div>

---

## Contents

- [What it does](#what-it-does)
- [Features](#features)
- [Requirements](#requirements)
- [Install](#install)
- [Usage](#usage)
- [Options](#options)
- [Output](#output)
- [How columns are detected](#how-columns-are-detected)
- [Tests](#tests)
- [Project structure](#project-structure)
- [License](#license)

## What it does

```
BPS CSV  ──▶  filter by region prefix  ──▶  aggregate kabupaten / kecamatan / desa
                                                      │
                                                      ▼
                                               pivot by gender
                                                      │
                                                      ▼
                                          Population_Data_Processed.xlsx
```

The input is the standard BPS export
`jumlah-penduduk-desa-berdasarkan-jenis-kelamin.csv` (semicolon separated). The
output is one sheet with a row for every administrative level.

## Features

- Filter by any region-code prefix (`--prefix 1103` for Aceh Selatan).
- Aggregate counts up from village level to sub-district and district level.
- Format region codes: `1103` → `11.03`, `110301` → `11.03.01`,
  `1103012001` → `11.03.01.2001`.
- Pivot `LAKI-LAKI`, `PEREMPUAN` and computed `TOTAL`.
- Resolve columns by **header name**, with the published BPS layout as a fallback.
- Fail loudly with an actionable message when a file or column is missing.

## Requirements

- Python 3.10+
- `pandas` and `openpyxl` (installed from `requirements.txt`)

## Install

```bash
git clone https://github.com/Zahrexxs/Process-Aceh-Population-Data.git
cd Process-Aceh-Population-Data

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
# source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

Put the CSV in the repository root and run:

```bash
python process_population.py
```

Or point at explicit paths:

```bash
python process_population.py \
  --input data/jumlah-penduduk-desa-berdasarkan-jenis-kelamin.csv \
  --output output/Population_Data_Processed.xlsx \
  --prefix 1105
```

## Options

| Option | Default | Description |
|---|---|---|
| `-i`, `--input` | `jumlah-penduduk-desa-berdasarkan-jenis-kelamin.csv` | Input CSV path |
| `-o`, `--output` | `Population_Data_Processed.xlsx` | Output Excel path |
| `-p`, `--prefix` | `1103` | Desa code prefix (Kabupaten/City) to keep |
| `--sep` | `;` | CSV delimiter |

## Output

| Column | Description |
|---|---|
| `KODE` | Formatted region code (kabupaten, kecamatan or desa) |
| `DESA` | Region name, matching the code level |
| `LAKI-LAKI` | Male population |
| `PEREMPUAN` | Female population |
| `TOTAL` | `LAKI-LAKI` + `PEREMPUAN` |

Rows are sorted by administrative hierarchy, so a district row is followed by its
sub-districts and their villages.

## How columns are detected

The script normalizes header names and looks for aliases such as
`kemendagri_kode_desa` or `kode_desa`. If a header is not recognized it falls back
to the published BPS column positions. If neither works, it stops with an error
that lists the columns it found, so you can fix the input instead of guessing.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite covers code formatting, aggregation totals across all three levels,
prefix filtering, validation errors, column resolution, and a full CLI round-trip
that writes and re-reads a real `.xlsx`. CI runs it on Python 3.12.

## Project structure

```
process_population.py   CLI, column resolution, aggregation and Excel export
tests/                  pytest suite
requirements.txt        runtime dependencies
requirements-dev.txt    runtime + pytest
pyproject.toml          pytest configuration
```

## License

[MIT](./LICENSE) © 2026 Muhammad Naufal Azzahri
