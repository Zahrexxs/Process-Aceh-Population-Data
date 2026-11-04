import pandas as pd
import pytest

from process_population import format_code, main, process_dataframe, resolve_columns

COLUMNS = [
    "provinsi_kode",
    "provinsi_nama",
    "kemendagri_kode_kabupaten",
    "kemendagri_nama_kabupaten",
    "kemendagri_kode_kecamatan",
    "kemendagri_nama_kecamatan",
    "kemendagri_kode_desa",
    "kemendagri_nama_desa",
    "spacer",
    "jenis_kelamin",
    "jumlah_penduduk_berdasarkan_jenis_kelamin",
]


def make_rows():
    return [
        ["11", "ACEH", "1103", "ACEH SELATAN", "110301", "LABUHAN HAJI", "1103012001", "DESA A", "", "Laki-Laki", "100"],
        ["11", "ACEH", "1103", "ACEH SELATAN", "110301", "LABUHAN HAJI", "1103012001", "DESA A", "", "Perempuan", "90"],
        ["11", "ACEH", "1103", "ACEH SELATAN", "110301", "LABUHAN HAJI", "1103012002", "DESA B", "", "Laki-Laki", "50"],
        ["11", "ACEH", "1103", "ACEH SELATAN", "110301", "LABUHAN HAJI", "1103012002", "DESA B", "", "Perempuan", "60"],
        ["11", "ACEH", "1103", "ACEH SELATAN", "110302", "BAKONGAN", "1103022001", "DESA C", "", "Laki-Laki", "10"],
        ["11", "ACEH", "1103", "ACEH SELATAN", "110302", "BAKONGAN", "1103022001", "DESA C", "", "Perempuan", "5"],
        ["11", "ACEH", "1104", "ACEH TENGGARA", "110401", "LAWE ALAS", "1104012001", "DESA D", "", "Laki-Laki", "999"],
        ["11", "ACEH", "1104", "ACEH TENGGARA", "110401", "LAWE ALAS", "1104012001", "DESA D", "", "Perempuan", "999"],
    ]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1103", "11.03"),
        ("110301", "11.03.01"),
        ("1103012001", "11.03.01.2001"),
        (" 1103 ", "11.03"),
        ("123", "123"),
    ],
)
def test_format_code(raw, expected):
    assert format_code(raw) == expected


def test_process_dataframe_aggregates_all_levels():
    df = pd.DataFrame(make_rows(), columns=COLUMNS)
    result = process_dataframe(df, "1103")

    assert list(result.columns) == ["KODE", "DESA", "LAKI-LAKI", "PEREMPUAN", "TOTAL"]
    assert len(result) == 6  # 1 kabupaten + 2 kecamatan + 3 desa

    by_code = result.set_index("KODE")
    assert by_code.loc["11.03", "TOTAL"] == 315
    assert by_code.loc["11.03.01", "TOTAL"] == 300
    assert by_code.loc["11.03.01.2001", "TOTAL"] == 190
    assert by_code.loc["11.03.01.2002", "TOTAL"] == 110
    assert by_code.loc["11.03.02.2001", "TOTAL"] == 15


def test_process_dataframe_filters_other_regions():
    df = pd.DataFrame(make_rows(), columns=COLUMNS)
    result = process_dataframe(df, "1103")

    assert not result["KODE"].astype(str).str.startswith("11.04").any()


def test_process_dataframe_rejects_empty_result():
    df = pd.DataFrame(make_rows(), columns=COLUMNS)

    with pytest.raises(ValueError, match="prefix '9999'"):
        process_dataframe(df, "9999")


def test_process_dataframe_reports_missing_columns():
    df = pd.DataFrame({"a": ["1"], "b": ["2"]})

    with pytest.raises(ValueError, match="Could not find a column"):
        process_dataframe(df, "1103")


def test_resolve_columns_uses_name_matching():
    columns = resolve_columns(COLUMNS)

    assert columns["kab_code"] == "kemendagri_kode_kabupaten"
    assert columns["desa_name"] == "kemendagri_nama_desa"
    assert columns["count"] == "jumlah_penduduk_berdasarkan_jenis_kelamin"


def test_cli_writes_excel_report(tmp_path):
    df = pd.DataFrame(make_rows(), columns=COLUMNS)
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "report.xlsx"
    df.to_csv(input_path, sep=";", index=False)

    exit_code = main(
        ["--input", str(input_path), "--output", str(output_path), "--prefix", "1103"]
    )

    assert exit_code == 0
    result = pd.read_excel(output_path)
    assert list(result.columns) == ["KODE", "DESA", "LAKI-LAKI", "PEREMPUAN", "TOTAL"]
    assert len(result) == 6


def test_cli_returns_error_for_missing_input(tmp_path):
    exit_code = main(["--input", str(tmp_path / "missing.csv")])

    assert exit_code == 1
