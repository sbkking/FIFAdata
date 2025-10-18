import json
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, inspect
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

CSV_DIR = Path(".")
DB_URI = "postgresql+psycopg2://sbk:2707@localhost:5432/fifa_db"
engine = create_engine(DB_URI, connect_args={"connect_timeout":10})
inspector = inspect(engine)

def get_table_columns(table_name):
    try:
        cols = inspector.get_columns(table_name, schema="fifa")
        return [c["name"] for c in cols]
    except Exception:
        return []

def sanitize_chunk(df):
    # Convert dict/list -> JSON string to avoid SQLAlchemy binding errors
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

def safe_load_to_table(csv_file, target_table, extra_cols=None):
    p = CSV_DIR / csv_file
    if not p.exists():
        print("Missing file:", csv_file)
        return
    print("Reading", csv_file)
    chunksize = 200000
    allowed_cols = get_table_columns(target_table)
    if not allowed_cols:
        print("Warning: no columns fetched for table", target_table)
    for chunk in pd.read_csv(p, chunksize=chunksize, low_memory=False):
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
                print("No matching columns between CSV and table", target_table, "- skipping chunk")
                continue
            chunk = chunk[cols_to_keep]
        chunk = chunk.where(pd.notnull(chunk), None)
        chunk.to_sql(target_table, engine, schema="fifa", if_exists="append", index=False, method="multi", chunksize=1000)
        print("Appended chunk to", target_table, "rows:", len(chunk))

if __name__ == "__main__":
    safe_load_to_table("male_teams.csv", "teams")
    safe_load_to_table("female_teams.csv", "teams")
    safe_load_to_table("male_coaches.csv", "coaches")
    safe_load_to_table("female_coaches.csv", "coaches")
    safe_load_to_table("male_players_small.csv", "players_staging", extra_cols={"gender":"male"})
    safe_load_to_table("female_players.csv", "players_staging", extra_cols={"gender":"female"})
    print("✅ Sanitized import finished!")
