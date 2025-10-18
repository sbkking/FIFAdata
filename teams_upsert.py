# teams_upsert.py
# Read male_teams.csv + female_teams.csv and upsert into fifa.teams
import csv, json
import pandas as pd
import numpy as np
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

CSV_DIR = Path(".")
DB_PARAMS = {"dbname":"fifa_db","user":"sbk","password":"2707","host":"localhost"}
BATCH = 500

def safe_val(v):
    # convert pandas/numpy / weird types -> python scalar or None
    try:
        if v is None:
            return None
        if isinstance(v, float) and np.isnan(v):
            return None
    except Exception:
        pass
    # if it's a list/dict/array convert to JSON string
    if isinstance(v, (dict, list, tuple, set, np.ndarray, pd.Series)):
        try:
            return json.dumps(v, ensure_ascii=False)
        except Exception:
            return str(v)
    # strip whitespace strings
    if isinstance(v, str):
        s = v.strip()
        return s if s != "" else None
    return v

def upsert_csv_to_teams(csv_file):
    p = CSV_DIR / csv_file
    if not p.exists():
        print("Missing", csv_file)
        return
    print("Upserting from", csv_file)
    # choose the columns we will upsert (these should exist or be NULL)
    cols = ["team_id","team_name","country","league","overall_rating","attack","midfield","defense","fifa_rank","founded_year","stadium"]
    insert_tmpl = "(" + ",".join(["%s"]*len(cols)) + ")"
    on_conflict_set = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols[1:]])  # skip team_id
    sql = f"INSERT INTO fifa.teams ({','.join(cols)}) VALUES %s ON CONFLICT (team_id) DO UPDATE SET {on_conflict_set};"

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # We'll use pandas to read in chunks and build batches of tuples
    for chunk in pd.read_csv(p, chunksize=200000, dtype=str, keep_default_na=False, na_values=["", "NA", "NaN"]):
        # simple column normalization: rename common alt-names
        chunk = chunk.rename(columns={'club':'club_name', 'team':'team_name', 'team_id':'team_id'})
        # Ensure columns exist in dataframe
        for c in cols:
            if c not in chunk.columns:
                chunk[c] = None
        # sanitize and convert types
        rows = []
        for i, row in chunk.iterrows():
            vals = []
            for c in cols:
                v = row.get(c, None)
                v = safe_val(v)
                # cast numeric-like to None or int later in SQL using NULLIF::int, but we'll pass strings
                vals.append(v)
            rows.append(tuple(vals))
            if len(rows) >= BATCH:
                execute_values(cur, sql, rows, template=None, page_size=BATCH)
                conn.commit()
                print("Upserted batch of", len(rows))
                rows = []
        if rows:
            execute_values(cur, sql, rows, template=None, page_size=BATCH)
            conn.commit()
            print("Upserted batch of", len(rows))
    cur.close()
    conn.close()
    print("Finished upserting", csv_file)

if __name__ == "__main__":
    upsert_csv_to_teams("male_teams.csv")
    upsert_csv_to_teams("female_teams.csv")
    print("✅ teams upsert finished")
