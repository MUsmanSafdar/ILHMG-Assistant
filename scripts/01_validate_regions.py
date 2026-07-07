import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
REGION_FILE = BASE_DIR / 'data' / 'processed' / 'illinois_county_regions.csv'

EXPECTED = {
    'Northeast': 12,
    'Northwest': 17,
    'Central': 34,
    'Southern': 39
}

df = pd.read_csv(REGION_FILE)

print('\nIllinois County Region Validation')
print('--------------------------------')
print(f'Total rows: {len(df)}')

blank = df['region'].isna().sum() + (df['region'].astype(str).str.strip() == '').sum()
print(f'Blank region rows: {blank}')

counts = df['region'].value_counts(dropna=False)
print('\nCurrent region counts:')
print(counts)

print('\nExpected region counts:')
for region, count in EXPECTED.items():
    actual = int((df['region'] == region).sum())
    status = 'OK' if actual == count else 'CHECK'
    print(f'{region}: {actual} / {count} {status}')

if len(df) != 102:
    print('\nERROR: County file should have 102 rows.')
else:
    print('\nCounty count is 102.')

missing_counties = df[df['region'].isna() | (df['region'].astype(str).str.strip() == '')]
if not missing_counties.empty:
    print('\nCounties still missing region assignment:')
    print(missing_counties[['county', 'county_fips']].to_string(index=False))
