# ⚽ FIFA Football Analytics Project

## 📘 Overview
This project is part of a Data Analytics course.  
It focuses on building and analyzing a PostgreSQL database using real FIFA datasets —  
including **male and female players, coaches, and teams**.

We use **Python** and **SQL** to explore performance statistics, build relationships between tables,  
and run analytical queries directly from the database.

---

## 🏢 Project Context
**Company:** Global Football Analytics  
We act as a data-driven sports insights company focused on football (both male and female leagues).  
The goal is to analyze:
- Player ratings, potentials, and transfer values  
- Team performance and structures  
- Coach demographics and club distribution  
- Relationships between players, coaches, and teams  

---

## 🗄️ Database Schema

```
        female_teams ───┬──▶ female_players
                         └──▶ female_coaches

        male_teams   ───┬──▶ male_players
                         └──▶ male_coaches
```

Each table is linked via `team_id`.

---

## 🧱 Technologies Used
- **PostgreSQL** — relational database
- **pgAdmin / psql** — for database management
- **Python (psycopg2, pandas)** — for connecting and querying
- **GitHub** — for version control

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/sbkking/FIFA-analytics.git
cd fifa-football-analytics
```

### 2️⃣ Create and configure PostgreSQL database
```sql
CREATE DATABASE fifa_db;
```

Then connect:
```bash
psql -U postgres -d fifa_db
```

### 3️⃣ Create all tables
Use the SQL schema or run these commands in `psql`:
```sql
\i schema.sql
```

*(This file contains all `CREATE TABLE` statements and foreign key relations.)*

---

### 4️⃣ Import CSV Data
```sql
\copy female_players(...) FROM 'C:/path/female_players.csv' DELIMITER ',' CSV HEADER ENCODING 'UTF8';
\copy female_teams(...) FROM 'C:/path/female_teams.csv' DELIMITER ',' CSV HEADER ENCODING 'UTF8';
\copy female_coaches(...) FROM 'C:/path/female_coaches.csv' DELIMITER ',' CSV HEADER ENCODING 'UTF8';

\copy male_players(...) FROM 'C:/path/male_players.csv' DELIMITER ',' CSV HEADER ENCODING 'UTF8';
\copy male_teams(...) FROM 'C:/path/male_teams.csv' DELIMITER ',' CSV HEADER ENCODING 'UTF8';
\copy male_coaches(...) FROM 'C:/path/male_coaches.csv' DELIMITER ',' CSV HEADER ENCODING 'UTF8';
```

---

### 5️⃣ Run Python script to test queries
```bash
python test_queries.py
```

This script:
- Connects to the database  
- Runs analytical queries (top players, team stats, averages, etc.)  
- Displays the results directly in the terminal

---

## 📊 Example Queries
Some of the analytics performed:

```sql
-- Top 10 female players
SELECT short_name, club_name, overall, potential
FROM female_players
ORDER BY overall DESC
LIMIT 10;

-- Average team rating by nationality
SELECT nationality_name, AVG(overall) AS avg_rating
FROM female_players
GROUP BY nationality_name
ORDER BY avg_rating DESC;
```

---

## 🧩 Folder Structure
```
/fifa-football-analytics
│
├── schema.sql
├── test_queries.py
├── README.md
│
├── /data
│   ├── female_players.csv
│   ├── female_teams.csv
│   ├── female_coaches.csv
│   ├── male_players.csv
│   ├── male_teams.csv
│   └── male_coaches.csv
│
└── /images
    └── main_analytics.png
```

---

## 💡 Notes
- If encoding errors occur (`UTF-8` vs `WIN1251`), open CSV files in Python and re-save with UTF-8:
  ```python
  import pandas as pd
  df = pd.read_csv("file.csv", encoding="utf-8", on_bad_lines='skip')
  df.to_csv("clean_file.csv", index=False, encoding="utf-8")
  ```

- Use `TRUNCATE TABLE table_name;` before reimporting to clear data.

---

## ✅ Run Summary
After setup, your system will:
1. Build the database  
2. Import male & female player, coach, and team data  
3. Establish relationships  
4. Execute Python-based queries  
5. Display analytics in the console  

---

👨‍💻 *Created by:* **Sbk Sbk**  
📅 *Project:* FIFA Football Analytics (Database & Data Querying)
