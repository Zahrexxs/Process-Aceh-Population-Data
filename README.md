# Aceh Population Data Processing

This script processes village-level population data (CSV) to generate a formatted Excel report. It specifically aggregates data to the Kabupaten (District) and Kecamatan (Sub-district) levels and formats region codes.

## Features

- Filters data for specific region prefixes (default `1103`).
- Aggregates population counts from Desa (Village) level to Kecamatan and Kabupaten levels.
- Formats region codes (e.g., `11.03`, `11.03.01`).
- Generates a pivoting Excel report with Male/Female/Total breakdowns.

## Prerequisites

- Python 3.x
- `pandas`
- `openpyxl`

## Setup

1. Clone this repository.
2. (Optional but recommended) Create a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install pandas openpyxl
    ```

## Usage

1. Place your input CSV file in the same directory.
    - Default expected filename: `jumlah-penduduk-desa-berdasarkan-jenis-kelamin.csv`
    - You can modify `process_population.py` to change `INPUT_FILE` if needed.
    - **Filtering**: To process a different Kabupaten/City, open `process_population.py` and change the `FILTER_PREFIX` variable (e.g., `FILTER_PREFIX = '1105'` for a different region code).

2. Run the script:

    ```bash
    python process_population.py
    ```

3. The output file `Population_Data_Processed.xlsx` will be generated in the same directory.
