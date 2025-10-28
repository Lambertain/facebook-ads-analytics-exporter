#!/usr/bin/env python3
"""Analyze Excel file from production."""
import pandas as pd
import sys

try:
    # Read all sheets
    excel_file = 'ecademy_meta_data_2025-10-23.xlsx'
    df_dict = pd.read_excel(excel_file, sheet_name=None)

    print("=" * 80)
    print("SHEETS IN FILE:")
    print("=" * 80)
    for sheet_name in df_dict.keys():
        print(f"  - {sheet_name}")

    print("\n" + "=" * 80)

    # Check STUDENTS sheet
    if 'Студенти' in df_dict:
        students_df = df_dict['Студенти']
        print("STUDENTS SHEET (Студенти):")
        print("=" * 80)
        print(f"Total rows: {len(students_df)}")
        print(f"Total columns: {len(students_df.columns)}")
        print("\nCOLUMNS:")
        for idx, col in enumerate(students_df.columns, 1):
            print(f"  {idx}. {col}")

        # Show first 3 rows with non-zero values
        print("\n" + "=" * 80)
        print("FIRST 3 ROWS (sample data):")
        print("=" * 80)
        print(students_df.head(3).to_string())

        # Check for columns with all zeros
        print("\n" + "=" * 80)
        print("COLUMNS WITH MOSTLY ZEROS:")
        print("=" * 80)
        for col in students_df.columns:
            if students_df[col].dtype in ['int64', 'float64']:
                zero_count = (students_df[col] == 0).sum()
                total_count = len(students_df[col])
                zero_percent = (zero_count / total_count * 100) if total_count > 0 else 0
                if zero_percent > 50:
                    print(f"  {col}: {zero_percent:.1f}% zeros ({zero_count}/{total_count})")

    else:
        print("ERROR: Sheet 'Студенти' not found!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
