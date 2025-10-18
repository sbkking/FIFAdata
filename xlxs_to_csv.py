# convert_xlsx_to_csv.py
import pandas as pd
from pathlib import Path

src = Path('.')  # current folder
for f in src.glob("*.xlsx"):
    print("Converting:", f.name)
    df = pd.read_excel(f, engine='openpyxl')
    out = f.with_suffix('.csv')
    df.to_csv(out, index=False)
    print("Saved:", out.name)
