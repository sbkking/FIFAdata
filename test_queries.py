import psycopg2

# ---------------------------
# 1️⃣ Connect to the database
# ---------------------------
try:
    conn = psycopg2.connect(
        dbname="fifa_db",
        user="postgres",
        password="1111",  # <-- замените на свой пароль
        host="localhost",
        port="5432"
    )
except Exception as e:
    print("Error connecting to database:", e)
    exit(1)

cur = conn.cursor()

# Принудительно устанавливаем UTF-8 для текущего соединения
cur.execute("SET client_encoding TO 'UTF8';")

# ---------------------------
# 2️⃣ SQL queries (10 аналитических)
# ---------------------------
queries = [
    ("Top 5 Female Players", "SELECT short_name, overall, club_name FROM female_players ORDER BY overall DESC LIMIT 5;"),
    ("Female Coaches Count by Nationality", "SELECT nationality_name, COUNT(*) FROM female_coaches GROUP BY nationality_name ORDER BY COUNT(*) DESC LIMIT 5;"),
    ("Average Age by Club", "SELECT club_name, ROUND(AVG(age),1) FROM female_players GROUP BY club_name ORDER BY AVG(age) DESC LIMIT 5;"),
    ("Total Wage by Club", "SELECT club_name, SUM(wage_eur) FROM female_players GROUP BY club_name ORDER BY SUM(wage_eur) DESC LIMIT 5;"),
    ("Players by Preferred Foot", "SELECT preferred_foot, COUNT(*) FROM female_players GROUP BY preferred_foot;"),
    ("Max & Min Potential by Club", "SELECT club_name, MAX(potential), MIN(potential) FROM female_players GROUP BY club_name LIMIT 5;"),
    ("Top 5 Coaches Alphabetically", "SELECT short_name, long_name FROM female_coaches ORDER BY short_name LIMIT 5;"),
    ("Highest Value Players", "SELECT short_name, value_eur, club_name FROM female_players ORDER BY value_eur DESC LIMIT 5;"),
    ("Average Overall by Nationality", "SELECT nationality_name, ROUND(AVG(overall),1) FROM female_players GROUP BY nationality_name ORDER BY ROUND(AVG(overall),1) DESC LIMIT 5;"),
    ("Players JOIN Coaches", "SELECT p.short_name AS player, c.short_name AS coach, p.club_name FROM female_players p LEFT JOIN female_coaches c ON p.club_name = c.nationality_name LIMIT 5;")
]

# ---------------------------
# 3️⃣ Execute and display
# ---------------------------
for title, query in queries:
    print(f"\n=== {title} ===")
    try:
        cur.execute(query)
        rows = cur.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print("Error executing query:", e)

# ---------------------------
# 4️⃣ Close connection
# ---------------------------
cur.close()
conn.close()
print("\n✅ All queries executed successfully.")
