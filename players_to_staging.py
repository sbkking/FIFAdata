# players_to_staging.py — load male_players_small.csv and female_players.csv into players_staging
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
        # normalize a few common names
        chunk = chunk.rename(columns={
            "sofifa_id":"player_id","sofifaID":"player_id","sofifaId":"player_id",
            "short_name":"player_name","long_name":"player_name",
            "club":"club_name","club_id":"club_id","team":"team_name"
        })
        # sanitize
        chunk = sanitize_chunk(chunk)
        if allowed_cols:
            cols_to_keep = [c for c in chunk.columns if c in allowed_cols]
            if not cols_to_keep:
                print("No matching columns for", csv_file, "- skipping")
                continue
            chunk = chunk[cols_to_keep]
        chunk = chunk.replace({"": None})
        # write in small batches
        for i in range(0, len(chunk), write_chunksize):
            sub = chunk.iloc[i:i+write_chunksize]
            sub.to_sql(table, engine, schema="fifa", if_exists="append", index=False, method=None)
            print("Appended", len(sub), "rows to", table)
    print("Finished", csv_file)

if __name__ == "__main__":
    load_players_to_staging("male_players_small.csv", "players_staging")
    load_players_to_staging("female_players.csv", "players_staging")
    print("✅ players -> staging finished")
