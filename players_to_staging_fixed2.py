# players_to_staging_fixed2.py — simpler robust loader that drops duplicate columns (case-insensitive)
import json, pandas as pd, numpy as np
from pathlib import Path
from sqlalchemy import create_engine, inspect
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

CSV_DIR = Path(".")
DB_URI = "postgresql+psycopg2://sbk:2707@localhost:5432/fifa_db"
engine = create_engine(DB_URI, connect_args={"connect_timeout":10})
inspector = inspect(engine)

def safe_val(v):
    try:
        if v is None:
            return None
        if isinstance(v, float) and np.isnan(v):
            return None
    except Exception:
        pass
    if isinstance(v, (dict, list, tuple, set, np.ndarray, pd.Series)):
        try:
            return json.dumps(v, ensure_ascii=False)
        except Exception:
            return str(v)
    if isinstance(v, str):
        s = v.strip()
        return s if s != "" else None
    return v

def sanitize_chunk(df):
    # Apply safe_val elementwise (vectorized apply is used per column)
    for col in df.columns:
        df[col] = df[col].apply(lambda v: safe_val(v))
    return df

def drop_duplicate_columns_case_insensitive(df):
    # Keep first occurrence, drop subsequent columns that duplicate (case-insensitive)
    cols = list(df.columns)
    lowered = [c.lower() if isinstance(c, str) else str(c) for c in cols]
    keep_mask = []
    seen = set()
    for i,key in enumerate(lowered):
        if key in seen:
            keep_mask.append(False)
        else:
            seen.add(key)
            keep_mask.append(True)
    # select only kept columns in original order
    keep_cols = [c for c,keep in zip(cols, keep_mask) if keep]
    if len(keep_cols) != len(cols):
        print(f"  Dropping {len(cols)-len(keep_cols)} duplicate column(s) in chunk")
    return df.loc[:, keep_cols]

def load_players_to_staging(csv_file, table='players_staging', read_chunksize=100000, write_chunksize=200):
    p = CSV_DIR / csv_file
    if not p.exists():
        print("Missing", csv_file); return
    print("Loading", csv_file)
    # allowed columns from DB
    try:
        cols_info = inspector.get_columns(table, schema="fifa")
        allowed_cols = [c["name"] for c in cols_info]
    except Exception:
        allowed_cols = []
    chunk_no = 0
    for chunk in pd.read_csv(p, chunksize=read_chunksize, low_memory=False, dtype=str, keep_default_na=False, na_values=["", "NA", "NaN"]):
        chunk_no += 1
        print(f" Chunk #{chunk_no} read, columns={len(chunk.columns)}")
        # normalize simple column names
        chunk = chunk.rename(columns={
            "sofifa_id":"player_id","sofifaID":"player_id","sofifaId":"player_id",
            "short_name":"player_name","long_name":"player_name",
            "club":"club_name","club_id":"club_id","team":"team_name"
        })
        # drop duplicate columns (case-insensitive), keep first
        chunk = drop_duplicate_columns_case_insensitive(chunk)
        # sanitize cell values
        chunk = sanitize_chunk(chunk)
        # keep only allowed columns if DB schema known
        if allowed_cols:
            cols_to_keep = [c for c in chunk.columns if c in allowed_cols]
            if not cols_to_keep:
                print(" No matching columns for", csv_file, "in this chunk - skipping")
                continue
            chunk = chunk[cols_to_keep]
        chunk = chunk.replace({"": None})
        # write in small batches
        rows_before = 0
        for i in range(0, len(chunk), write_chunksize):
            sub = chunk.iloc[i:i+write_chunksize]
            sub.to_sql(table, engine, schema="fifa", if_exists="append", index=False, method=None)
            rows_before += len(sub)
            print(f"  Appended {len(sub)} rows to {table}")
        print(f" Chunk #{chunk_no} finished, appended {rows_before} rows")
    print("Finished", csv_file)

if __name__ == "__main__":
    load_players_to_staging("male_players_small.csv", "players_staging")
    load_players_to_staging("female_players.csv", "players_staging")
    print("✅ players -> staging finished")
