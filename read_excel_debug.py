"""Debug script to read Excel export from UI."""
import pandas as pd

# Read Excel file
df = pd.read_excel(r'D:\Automation\Скрины\ecademy_meta_data_2025-10-21.xlsx', sheet_name='СТУДЕНТЫ')

print(f"Total rows: {len(df)}")
print(f"\nTotal columns: {len(df.columns)}")
print("\nAll columns:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")

print("\n" + "="*80)
print("FIRST ROW DATA:")
print("="*80)
for col in df.columns:
    val = df.iloc[0][col]
    print(f"{col}: {val}")

print("\n" + "="*80)
print("STATUS COLUMNS (first 3 rows):")
print("="*80)
status_cols = [c for c in df.columns if 'status_' in str(c).lower()]
print(f"Found {len(status_cols)} status columns")
if status_cols:
    print(df[status_cols].head(3).to_string())

print("\n" + "="*80)
print("KEY METRICS (first 3 rows):")
print("="*80)
key_cols = ['campaign_name', 'leads_count', 'contacted', 'in_progress', 'purchased', 'status_13', 'status_32', 'status_4']
available_key_cols = [c for c in key_cols if c in df.columns]
print(df[available_key_cols].head(3).to_string())
