import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

CSV_DIR = Path(".")
DB_URI = "postgresql+psycopg2://sbk:2707@localhost:5432/fifa_db"
engine = create_engine(DB_URI, connect_args={"connect_timeout":10})

def safe_load(csv_file, table_name, extra_cols=None):
    p = CSV_DIR / csv_file
    if not p.exists():
        print("Missing file:", csv_file)
        return
    print("Reading", csv_file)
    chunksize = 200000
    for chunk in pd.read_csv(p, chunksize=chunksize, low_memory=False):
        chunk = chunk.rename(columns={
            "sofifa_id":"player_id", "sofifaID":"player_id", "sofifaId":"player_id",
            "short_name":"player_name", "long_name":"player_name",
            "club":"club_name", "club_id":"club_id", "team":"team_name"
        })
        if extra_cols:
            for k,v in extra_cols.items():
                chunk[k] = v
        for col in ["value_eur","wage_eur"]:
            if col in chunk.columns:
                chunk[col] = chunk[col].astype(str).str.replace("[^0-9.-]", "", regex=True)
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce").fillna(0)
        chunk.to_sql(table_name, engine, schema="fifa", if_exists="append", index=False, method="multi", chunksize=1000)
        print("Appended chunk to", table_name, "rows:", len(chunk))

if __name__ == "__main__":
    safe_load("male_teams.csv", "teams")
    safe_load("female_teams.csv", "teams")
    safe_load("male_coaches.csv", "coaches")
    safe_load("female_coaches.csv", "coaches")
    safe_load("male_players_small.csv", "players", extra_cols={"gender":"male"})
    safe_load("female_players.csv", "players", extra_cols={"gender":"female"})
    print("✅ Import finished!")
