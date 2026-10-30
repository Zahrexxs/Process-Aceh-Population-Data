"""Aggregate Aceh village-level population data into a Kabupaten/Kecamatan/Desa report.

Reads the BPS village population CSV (semicolon separated), filters by region
code prefix, aggregates counts to kabupaten and kecamatan level, and writes a
formatted Excel file with Male/Female/Total columns.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

DEFAULT_INPUT = "jumlah-penduduk-desa-berdasarkan-jenis-kelamin.csv"
DEFAULT_OUTPUT = "Population_Data_Processed.xlsx"
DEFAULT_PREFIX = "1103"

# Header aliases, matched case-insensitively against normalized column names.
COLUMN_ALIASES = {
    "kab_code": ("kemendagri_kode_kabupaten", "kode_kabupaten", "kode_kab"),
    "kab_name": ("kemendagri_nama_kabupaten", "nama_kabupaten", "kabupaten"),
    "kec_code": ("kemendagri_kode_kecamatan", "kode_kecamatan", "kode_kec"),
    "kec_name": ("kemendagri_nama_kecamatan", "nama_kecamatan", "kecamatan"),
    "desa_code": ("kemendagri_kode_desa", "kode_desa"),
    "desa_name": ("kemendagri_nama_desa", "nama_desa", "desa"),
    "gender": ("jenis_kelamin", "gender"),
    "count": (
        "jumlah_penduduk_berdasarkan_jenis_kelamin",
        "jumlah_penduduk",
        "jumlah",
    ),
}

# Positional fallback for the published BPS export layout.
FALLBACK_POSITIONS = {
    "kab_code": 2,
    "kab_name": 3,
    "kec_code": 4,
    "kec_name": 5,
    "desa_code": 6,
    "desa_name": 7,
    "gender": 9,
    "count": 10,
}

FINAL_COLUMNS = ["KODE", "DESA", "LAKI-LAKI", "PEREMPUAN", "TOTAL"]


def format_code(code_str: str) -> str:
    """Format 1103012001 -> 11.03.01.2001, 110301 -> 11.03.01, 1103 -> 11.03."""
    value = str(code_str).strip()

    if len(value) == 4:
        return f"{value[:2]}.{value[2:]}"
    if len(value) == 6:
        return f"{value[:2]}.{value[2:4]}.{value[4:]}"
    if len(value) == 10:
        return f"{value[:2]}.{value[2:4]}.{value[4:6]}.{value[6:]}"

    return value


def _normalize(name: str) -> str:
    return str(name).strip().lower().replace("\n", "").replace(" ", "_")


def resolve_columns(columns: list[str]) -> dict[str, str]:
    """Map logical fields to actual CSV column names.

    Matching is done by alias first, then by normalized substring, and finally by
    the known BPS column positions. Raises ValueError with actionable context if
    a required column cannot be found.
    """
    normalized = {_normalize(col): col for col in columns}
    resolved: dict[str, str] = {}

    for field, aliases in COLUMN_ALIASES.items():
        match = next((normalized[a] for a in aliases if a in normalized), None)

        if match is None:
            match = next(
                (
                    original
                    for normalized_name, original in normalized.items()
                    if any(alias in normalized_name for alias in aliases)
                ),
                None,
            )

        if match is None:
            position = FALLBACK_POSITIONS.get(field)
            if position is not None and position < len(columns):
                match = columns[position]

        if match is None:
            raise ValueError(
                f"Could not find a column for '{field}'. "
                f"Available columns: {list(columns)}"
            )

        resolved[field] = match

    return resolved


def _normalize_gender(value: str) -> str:
    text = str(value).strip().lower()
    if "laki" in text:
        return "LAKI-LAKI"
    if "perempuan" in text:
        return "PEREMPUAN"
    return str(value).strip()


def process_dataframe(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Filter and aggregate a raw population dataframe.

    Returns a dataframe with columns KODE, DESA, LAKI-LAKI, PEREMPUAN, TOTAL
    containing kabupaten, kecamatan, and desa rows.
    """
    if df.empty:
        raise ValueError("Input CSV contains no rows.")

    df = df.copy()
    df.columns = [_normalize(c) for c in df.columns]
    columns = resolve_columns(list(df.columns))

    for field in ("desa_code", "kab_code", "kec_code"):
        df[columns[field]] = df[columns[field]].astype(str).str.strip()

    filtered = df[df[columns["desa_code"]].str.startswith(str(prefix))].copy()
    if filtered.empty:
        raise ValueError(f"No rows matched desa code prefix '{prefix}'.")

    filtered[columns["count"]] = (
        pd.to_numeric(filtered[columns["count"]], errors="coerce").fillna(0).astype(int)
    )
    filtered[columns["gender"]] = filtered[columns["gender"]].map(_normalize_gender)

    levels = [
        (columns["kab_code"], columns["kab_name"]),
        (columns["kec_code"], columns["kec_name"]),
        (columns["desa_code"], columns["desa_name"]),
    ]

    frames = []
    for code_col, name_col in levels:
        grouped = (
            filtered.groupby([code_col, name_col, columns["gender"]], as_index=False)[
                columns["count"]
            ]
            .sum()
            .rename(columns={code_col: "KODE", name_col: "DESA"})
        )
        frames.append(grouped)

    combined = pd.concat(frames, ignore_index=True)
    combined["KODE"] = (
        combined["KODE"].astype(str).str.replace(".", "", regex=False).str.strip()
    )

    pivot = combined.pivot_table(
        index=["KODE", "DESA"],
        columns=columns["gender"],
        values=columns["count"],
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for gender in ("LAKI-LAKI", "PEREMPUAN"):
        if gender not in pivot.columns:
            pivot[gender] = 0

    pivot["TOTAL"] = pivot["LAKI-LAKI"] + pivot["PEREMPUAN"]
    pivot = pivot.sort_values(by="KODE")
    pivot["KODE"] = pivot["KODE"].apply(format_code)

    return pivot[FINAL_COLUMNS]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate Aceh village population data into an Excel report."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=DEFAULT_INPUT,
        help=f"Input CSV file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output Excel file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        default=DEFAULT_PREFIX,
        help=f"Desa code prefix to keep (default: {DEFAULT_PREFIX})",
    )
    parser.add_argument(
        "--sep",
        default=";",
        help="CSV delimiter (default: ';')",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    print(f"Reading {input_path}...")
    df = pd.read_csv(input_path, sep=args.sep, dtype=str)

    try:
        result = process_dataframe(df, args.prefix)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Found {len(result)} aggregated rows.")
    print("Preview of final data:")
    print(result.head())

    output_path = Path(args.output)
    print(f"Saving to {output_path}...")
    result.to_excel(output_path, index=False)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
