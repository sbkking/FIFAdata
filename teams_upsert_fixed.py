# teams_upsert_fixed.py
# Robust upsert that deduplicates by team_id inside each batch to avoid ON CONFLICT cardinality errors.
import json, pandas as pd, numpy as np
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

CSV_DIR = Path(".")
DB_PARAMS = {"dbname":"fifa_db","user":"sbk","password":"2707","host":"localhost"}
BATCH = 300  # smaller batch for safety

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

def upsert_csv_to_teams(csv_file):
    p = CSV_DIR / csv_file
    if not p.exists():
        print("Missing", csv_file)
        return
    print("Upserting from", csv_file)
    cols = ["team_id","team_name","country","league","overall_rating","attack","midfield","defense","fifa_rank","founded_year","stadium"]
    on_conflict_set = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols[1:]])  # skip team_id
    sql = f"INSERT INTO fifa.teams ({','.join(cols)}) VALUES %s ON CONFLICT (team_id) DO UPDATE SET {on_conflict_set};"

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for chunk in pd.read_csv(p, chunksize=200000, dtype=str, keep_default_na=False, na_values=["", "NA", "NaN"]):
        # ensure columns exist
        for c in cols:
            if c not in chunk.columns:
                chunk[c] = None

        rows = []
        for i, row in chunk.iterrows():
            vals = tuple(safe_val(row.get(c, None)) for c in cols)
            rows.append(vals)
            if len(rows) >= BATCH:
                # dedupe by team_id keeping last occurrence
                dedup = {}
                for r in rows:
                    key = r[0]  # team_id
                    dedup[key] = r
                dedup_rows = list(dedup.values())
                execute_values(cur, sql, dedup_rows, template=None, page_size=BATCH)
                conn.commit()
                print("Upserted batch of", len(dedup_rows))
                rows = []
        # remaining rows
        if rows:
            dedup = {}
            for r in rows:
                key = r[0]
                dedup[key] = r
            dedup_rows = list(dedup.values())
            execute_values(cur, sql, dedup_rows, template=None, page_size=BATCH)
            conn.commit()
            print("Upserted batch of", len(dedup_rows))
    cur.close()
    conn.close()
    print("Finished upserting", csv_file)

if __name__ == "__main__":
    upsert_csv_to_teams("male_teams.csv")
    upsert_csv_to_teams("female_teams.csv")
    print("✅ teams upsert fixed finished")
