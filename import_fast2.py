# import_fast2.py — robust importer (fallbacks and safer sanitizer)
import json
import pandas as pd
import numpy as np
from pathlib import Path
import psycopg2
from sqlalchemy import create_engine, inspect
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

CSV_DIR = Path(".")
DB_URI_SQLA = "postgresql+psycopg2://sbk:2707@localhost:5432/fifa_db"
engine = create_engine(DB_URI_SQLA, connect_args={"connect_timeout":10})
inspector = inspect(engine)

def get_table_columns(table_name):
    try:
        cols = inspector.get_columns(table_name, schema="fifa")
        return [c["name"] for c in cols]
    except Exception:
        return []

def safe_scalar_to_text(x):
    # robust conversion for one cell
    # treat pandas NA/np.nan, None -> None
    try:
        if x is None:
            return None
        # pandas NA (pd.NA) and numpy nan
        if (isinstance(x, float) and np.isnan(x)) or x is pd.NA:
            return None
    except Exception:
        pass
    # If the value is a list/dict/array/Series -> JSON string
    if isinstance(x, (dict, list, tuple, set, np.ndarray, pd.Series)):
        try:
            return json.dumps(x, ensure_ascii=False)
        except Exception:
            return str(x)
    # If it's a string that looks like list/dict, still keep as-is
    # Otherwise return as-is
    return x

def sanitize_chunk(df):
    # Convert problematic cell types to safe scalars
    for col in df.columns:
        # apply conversion elementwise but robustly
        df[col] = df[col].apply(lambda v: safe_scalar_to_text(v))
    return df

def load_with_pandas(csv_path, target_table, extra_cols=None, read_chunksize=200000, write_chunksize=500):
    p = CSV_DIR / csv_path
    if not p.exists():
        print("Missing file:", csv_path)
        return
    print("Loading via pandas:", csv_path, "->", target_table)
    allowed_cols = get_table_columns(target_table)
    for chunk in pd.read_csv(p, chunksize=read_chunksize, low_memory=False, dtype=str, keep_default_na=False, na_values=["", "NA", "NaN"]):
        # rename common columns if present
        chunk = chunk.rename(columns={
            "sofifa_id":"player_id", "sofifaID":"player_id", "sofifaId":"player_id",
            "short_name":"player_name", "long_name":"player_name",
            "club":"club_name", "club_id":"club_id", "team":"team_name"
        })
        if extra_cols:
            for k,v in extra_cols.items():
                chunk[k] = v
        # sanitize weird cells
        chunk = sanitize_chunk(chunk)
        # Filter allowed columns if we can
        if allowed_cols:
            cols_to_keep = [c for c in chunk.columns if c in allowed_cols]
            if not cols_to_keep:
                print("No matching columns for", target_table, "- skipping chunk")
                continue
            chunk = chunk[cols_to_keep]
        # replace empty strings with None
        chunk = chunk.replace({"": None})
        # write smaller batches to avoid huge multi-row insert parameters
        for start in range(0, len(chunk), write_chunksize):
            sub = chunk.iloc[start:start+write_chunksize]
            sub.to_sql(target_table, engine, schema="fifa", if_exists="append", index=False, method=None)
            print(f"Appended {len(sub)} rows to {target_table}")
    print("Finished loading", csv_path, "->", target_table)

# Keep the COPY helper in case you want it later (unused here)
def copy_csv_to_table(csv_path, table_name, cols=None):
    conn = None
    try:
        conn = psycopg2.connect("dbname=fifa_db user=sbk password=2707 host=localhost")
        cur = conn.cursor()
        with open(csv_path, "r", encoding="utf-8") as f:
            if cols:
                col_list = ",".join(cols)
                sql = f"COPY fifa.{table_name} ({col_list}) FROM STDIN WITH CSV HEADER DELIMITER ',' NULL ''"
            else:
                sql = f"COPY fifa.{table_name} FROM STDIN WITH CSV HEADER DELIMITER ',' NULL ''"
            cur.copy_expert(sql, f)
        conn.commit()
        cur.close()
        print(f"COPY success -> {table_name}")
    except Exception as e:
        print("COPY failed for", table_name, ":", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Use pandas loader for teams & coaches (safer with variable CSVs)
    load_with_pandas("male_teams.csv", "teams")
    load_with_pandas("female_teams.csv", "teams")
    load_with_pandas("male_coaches.csv", "coaches")
    load_with_pandas("female_coaches.csv", "coaches")

    # Players -> staging with small insert batches
    load_with_pandas("male_players_small.csv", "players_staging", extra_cols={"gender":"male"}, read_chunksize=200000, write_chunksize=200)
    load_with_pandas("female_players.csv",    "players_staging", extra_cols={"gender":"female"}, read_chunksize=200000, write_chunksize=200)
    print("✅ Robust import finished!")
