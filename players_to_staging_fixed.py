# players_to_staging_fixed.py — robust loader that removes duplicate columns before inserting
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
    for col in df.columns:
        df[col] = df[col].apply(lambda v: safe_val(v))
    return df

def normalize_and_dedupe_columns(df):
    # Normalize column names (strip) and remove duplicates case-insensitively,
    # keeping the first occurrence.
    new_cols = []
    seen = {}
    for col in df.columns:
        if isinstance(col, str):
            norm = col.strip()
        else:
            norm = col
        key = str(norm).lower()  # case-insensitive key
        if key in seen:
            # duplicate: skip this column (drop it)
            continue
        seen[key] = norm
        new_cols.append(norm)
    # Reindex df to keep only first occurrences in original order that survived dedupe
    # But we need to preserve actual column values under the chosen column name:
    # Build a mapping from old column to new normalized name for kept columns.
    mapping = {}
    kept = []
    used_keys = set()
    for col in df.columns:
        key = str(col).strip().lower() if isinstance(col, str) else str(col)
        if key in used_keys:
            continue
        used_keys.add(key)
        mapped_name = seen[key]
        mapping[col] = mapped_name
        kept.append(col)
    # Rename kept columns to normalized names
    df2 = df[kept].rename(columns=mapping)
    return df2

def load_players_to_staging(csv_file, table='players_staging', read_chunksize=100000, write_chunksize=200):
    p = CSV_DIR / csv_file
    if not p.exists():
        print("Missing", csv_file); return
    print("Loading", csv_file)
    # get allowed columns
    try:
        cols_info = inspector.get_columns(table, schema="fifa")
        allowed_cols = [c["name"] for c in cols_info]
    except Exception:
        allowed_cols = []
    for chunk in pd.read_csv(p, chunksize=read_chunksize, low_memory=False, dtype=str, keep_default_na=False, na_values=["", "NA", "NaN"]):
        # normalize a few common names (these will be deduped/normalized next)
        chunk = chunk.rename(columns={
            "sofifa_id":"player_id","sofifaID":"player_id","sofifaId":"player_id",
            "short_name":"player_name","long_name":"player_name",
            "club":"club_name","club_id":"club_id","team":"team_name"
        })
        # Remove duplicate columns and normalize names
        chunk = normalize_and_dedupe_columns(chunk)
        # sanitize cell values
        chunk = sanitize_chunk(chunk)
        if allowed_cols:
            cols_to_keep = [c for c in chunk.columns if c in allowed_cols]
            if not cols_to_keep:
                print("No matching columns for", csv_file, "- skipping this chunk")
                continue
            chunk = chunk[cols_to_keep]
        chunk = chunk.replace({"": None})
        # write in small batches to avoid huge parameter lists
        for i in range(0, len(chunk), write_chunksize):
            sub = chunk.iloc[i:i+write_chunksize]
            sub.to_sql(table, engine, schema="fifa", if_exists="append", index=False, method=None)
            print("Appended", len(sub), "rows to", table)
    print("Finished", csv_file)

if __name__ == "__main__":
    load_players_to_staging("male_players_small.csv", "players_staging")
    load_players_to_staging("female_players.csv", "players_staging")
    print("✅ players -> staging finished")
