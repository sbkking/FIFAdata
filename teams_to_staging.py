import json, pandas as pd, numpy as np
from pathlib import Path
from sqlalchemy import create_engine, inspect
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

CSV_DIR = Path(".")
DB_URI = "postgresql+psycopg2://sbk:2707@localhost:5432/fifa_db"
engine = create_engine(DB_URI, connect_args={"connect_timeout":10})
inspector = inspect(engine)

def safe_scalar_to_text(x):
    try:
        if x is None:
            return None
        if (isinstance(x, float) and np.isnan(x)) or x is pd.NA:
            return None
    except Exception:
        pass
    if isinstance(x, (dict, list, tuple, set, np.ndarray, pd.Series)):
        try:
            return json.dumps(x, ensure_ascii=False)
        except Exception:
            return str(x)
    return x

def sanitize_chunk(df):
    for col in df.columns:
        df[col] = df[col].apply(lambda v: safe_scalar_to_text(v))
    return df

def load_csv_to_staging(csv_file, table, read_chunksize=200000, write_chunksize=200):
    p = CSV_DIR / csv_file
    if not p.exists():
        print("Missing", csv_file); return
    print("Loading", csv_file)
    cols_info = inspector.get_columns(table, schema="fifa")
    allowed_cols = [c["name"] for c in cols_info]
    for chunk in pd.read_csv(p, chunksize=read_chunksize, low_memory=False, dtype=str, keep_default_na=False, na_values=["", "NA", "NaN"]):
        chunk = chunk.rename(columns={'club':'club_name','club_id':'club_id','team':'team_name'})
        chunk = sanitize_chunk(chunk)
        cols_to_keep = [c for c in chunk.columns if c in allowed_cols]
        if not cols_to_keep:
            print("No matching columns for", csv_file, "- skipping")
            continue
        chunk = chunk[cols_to_keep].replace({'': None})
        for i in range(0, len(chunk), write_chunksize):
            sub = chunk.iloc[i:i+write_chunksize]
            sub.to_sql(table, engine, schema='fifa', if_exists='append', index=False, method=None)
            print("Appended", len(sub), "rows to", table)
    print("Finished", csv_file)

if __name__ == '__main__':
    load_csv_to_staging('male_teams.csv', 'teams_staging')
    load_csv_to_staging('female_teams.csv', 'teams_staging')
    print('✅ teams -> staging done')
