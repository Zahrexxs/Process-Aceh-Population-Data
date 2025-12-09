import pandas as pd
import os

# Configuration
INPUT_FILE = 'jumlah-penduduk-desa-berdasarkan-jenis-kelamin.csv'
OUTPUT_FILE = 'Population_Data_Processed.xlsx'
FILTER_PREFIX = '1103'

def format_code(code_str):
    """Formats 1103012001 to 11.03.01.2001, 110301 to 11.03.01, 1103 to 11.03"""
    # Ensure it's a string and strip whitespace
    s = str(code_str).strip()
    
    if len(s) == 4:
        return f"{s[:2]}.{s[2:]}"
    elif len(s) == 6:
        return f"{s[:2]}.{s[2:4]}.{s[4:]}"
    elif len(s) == 10:
        return f"{s[:2]}.{s[2:4]}.{s[4:6]}.{s[6:]}"
    
    return s

def main():
    print(f"Reading {INPUT_FILE}...")
    try:
        # Read CSV with semicolon delimiter
        df = pd.read_csv(INPUT_FILE, sep=';', dtype=str)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    # Normalize column names (strip whitespace/newlines from headers)
    df.columns = df.columns.str.replace('\n', '', regex=True).str.strip()

    # Identify columns by expected index from inspection
    # Index 6: Desa Code ('kemendagri_kode_desa')
    # Index 7: Desa Name ('kemendagri_nama_desa')
    # Index 9: Gender ('jenis_kelamin')
    # Index 10: Count ('jumlah_penduduk_berdasarkan_jenis_kelamin')
    
    col_kab_code = df.columns[2]
    col_kab_name = df.columns[3]
    col_kec_code = df.columns[4]
    col_kec_name = df.columns[5]
    col_desa_code = df.columns[6]
    col_desa_name = df.columns[7]
    col_gender = df.columns[9]
    col_count = df.columns[10]

    print(f"Filtering for desa code starting with {FILTER_PREFIX}...")
    # Filter data
    # Ensure desa code is treated as string
    df[col_desa_code] = df[col_desa_code].astype(str)
    mask = df[col_desa_code].str.startswith(FILTER_PREFIX)
    filtered_df = df[mask].copy()

    if filtered_df.empty:
        print("No matching data found!")
        return
    
    print(f"Found {len(filtered_df)} rows. Processing...")

    # Clean count column
    filtered_df[col_count] = pd.to_numeric(filtered_df[col_count], errors='coerce').fillna(0).astype(int)

    # 1. Aggregate Kabupaten Level
    # Group by Kab Code, Kab Name, Gender
    kab_group = filtered_df.groupby([col_kab_code, col_kab_name, col_gender], as_index=False)[col_count].sum()
    kab_group = kab_group.rename(columns={col_kab_code: 'KODE', col_kab_name: 'DESA'}) # Map Name to DESA col for uniformity

    # 2. Aggregate Kecamatan Level
    # Group by Kec Code, Kec Name, Gender
    kec_group = filtered_df.groupby([col_kec_code, col_kec_name, col_gender], as_index=False)[col_count].sum()
    kec_group = kec_group.rename(columns={col_kec_code: 'KODE', col_kec_name: 'DESA'})

    # 3. Prepare Desa Level
    desa_group = filtered_df[[col_desa_code, col_desa_name, col_gender, col_count]].copy()
    desa_group = desa_group.rename(columns={col_desa_code: 'KODE', col_desa_name: 'DESA'})

    # 4. Combine all levels
    combined_df = pd.concat([kab_group, kec_group, desa_group], ignore_index=True)

    # Clean KODE (remove any dots if present in input before formatting)
    combined_df['KODE'] = combined_df['KODE'].astype(str).str.replace('.', '', regex=False).str.strip()

    # Pivot table
    pivot = combined_df.pivot_table(
        index=['KODE', 'DESA'], 
        columns=col_gender, 
        values=col_count, 
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Normalize gender columns
    pivot_cols = list(pivot.columns)
    column_mapping = {} # Already have KODE and DESA
    
    lakilaki_col = next((c for c in pivot_cols if 'laki' in str(c).lower()), None)
    perempuan_col = next((c for c in pivot_cols if 'perempuan' in str(c).lower()), None)

    if lakilaki_col:
        column_mapping[lakilaki_col] = 'LAKI-LAKI'
    else:
        pivot['LAKI-LAKI'] = 0

    if perempuan_col:
        column_mapping[perempuan_col] = 'PEREMPUAN'
    else:
        pivot['PEREMPUAN'] = 0

    pivot = pivot.rename(columns=column_mapping)

    # Ensure columns exist
    for required in ['LAKI-LAKI', 'PEREMPUAN']:
        if required not in pivot.columns:
            pivot[required] = 0

    # Calculate TOTAL
    pivot['TOTAL'] = pivot['LAKI-LAKI'] + pivot['PEREMPUAN']
    
    # Sort by raw KODE to ensure hierarchy (1103 < 110301 < 1103012001)
    pivot = pivot.sort_values(by='KODE')

    # Apply formatting
    pivot['KODE'] = pivot['KODE'].apply(format_code)

    # Select final columns
    final_cols = ['KODE', 'DESA', 'LAKI-LAKI', 'PEREMPUAN', 'TOTAL']
    final_df = pivot[final_cols]

    print("Preview of final data:")
    print(final_df.head())

    print(f"Saving to {OUTPUT_FILE}...")
    final_df.to_excel(OUTPUT_FILE, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
