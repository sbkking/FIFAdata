import json
import pandas as pd
from pathlib import Path
import psycopg2
from sqlalchemy import create_engine, inspect
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

CSV_DIR = Path(".")
DB_URI_SQLA = "postgresql+psycopg2://sbk:2707@localhost:5432/fifa_db"
engine = create_engine(DB_URI_SQLA, connect_args={"connect_timeout":10})
inspector = inspect(engine)

# ---------- helper: sanitize dict/list -> JSON ----------
def sanitize_chunk(df):
    for col in df.select_dtypes(include=["object"]).columns:
        def _conv(x):
            if pd.isna(x):
                return None
            if isinstance(x, (dict, list)):
                try:
                    return json.dumps(x, ensure_ascii=False)
                except Exception:
                    return str(x)
            return x
        df[col] = df[col].apply(_conv)
    return df

# ---------- helper: get columns from DB ----------
def get_table_columns(table_name):
    try:
        cols = inspector.get_columns(table_name, schema="fifa")
        return [c["name"] for c in cols]
    except Exception:
        return []

# ---------- Fast COPY using psycopg2 (for whole CSV) ----------
def copy_csv_to_table(csv_path, table_name, cols=None):
    # cols = list of columns in correct order (optional)
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

# ---------- Safe load for staging using pandas (small chunks, method=None) ----------
def load_csv_to_staging(csv_file, target_table, extra_cols=None, read_chunksize=200000, write_chunksize=500):
    p = CSV_DIR / csv_file
    if not p.exists():
        print("Missing file:", csv_file)
        return
    print("Reading", csv_file, "-> staging table", target_table)
    allowed_cols = get_table_columns(target_table)
    # read in chunks and write small batches with executemany (method=None)
    for chunk in pd.read_csv(p, chunksize=read_chunksize, low_memory=False):
        chunk = chunk.rename(columns={
            "sofifa_id":"player_id", "sofifaID":"player_id", "sofifaId":"player_id",
            "short_name":"player_name", "long_name":"player_name",
            "club":"club_name", "club_id":"club_id", "team":"team_name"
        })
        if extra_cols:
            for k,v in extra_cols.items():
                chunk[k] = v
        chunk = sanitize_chunk(chunk)
        if allowed_cols:
            cols_to_keep = [c for c in chunk.columns if c in allowed_cols]
            if not cols_to_keep:
                print("No matching columns for", target_table, "- skipping chunk")
                continue
            chunk = chunk[cols_to_keep]
        chunk = chunk.where(pd.notnull(chunk), None)
        # write in smaller subchunks to avoid giant multi-row INSERTs
        for start in range(0, len(chunk), write_chunksize):
            sub = chunk.iloc[start:start+write_chunksize]
            sub.to_sql(target_table, engine, schema="fifa", if_exists="append", index=False, method=None)
            print(f"Appended {len(sub)} rows to {target_table}")
    print(f"Finished loading {csv_file} -> {target_table}")

if __name__ == "__main__":
    # 1) Fast COPY for teams and coaches (fewer mapping headaches)
    # We try to determine DB columns and use them; if mismatch, COPY may fail - fallback below
    teams_cols = get_table_columns("teams")
    coaches_cols = get_table_columns("coaches")
    try:
        copy_csv_to_table("male_teams.csv", "teams", cols=teams_cols if teams_cols else None)
    except Exception as e:
        print("COPY fallback for male_teams:", e)
        load_csv_to_staging("male_teams.csv", "teams")
    try:
        copy_csv_to_table("female_teams.csv", "teams", cols=teams_cols if teams_cols else None)
    except Exception as e:
        print("COPY fallback for female_teams:", e)
        load_csv_to_staging("female_teams.csv", "teams")

    try:
        copy_csv_to_table("male_coaches.csv", "coaches", cols=coaches_cols if coaches_cols else None)
    except Exception as e:
        print("COPY fallback for male_coaches:", e)
        load_csv_to_staging("male_coaches.csv", "coaches")
    try:
        copy_csv_to_table("female_coaches.csv", "coaches", cols=coaches_cols if coaches_cols else None)
    except Exception as e:
        print("COPY fallback for female_coaches:", e)
        load_csv_to_staging("female_coaches.csv", "coaches")

    # 2) players -> staging using smaller write batches (avoids huge param lists)
    load_csv_to_staging("male_players_small.csv", "players_staging", extra_cols={"gender":"male"}, read_chunksize=200000, write_chunksize=200)
    load_csv_to_staging("female_players.csv",    "players_staging", extra_cols={"gender":"female"}, read_chunksize=200000, write_chunksize=200)
    print("✅ Fast import finished!")
