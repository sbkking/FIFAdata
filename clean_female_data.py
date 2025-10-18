import pandas as pd

# -------------------------------
# 1️⃣ Очистка female_players
# -------------------------------
players_file = "female_players_simple_nodup_utf8.csv"
players_clean_file = "female_players_simple_nodup_utf8_final.csv"

# Загружаем CSV, пропуская битые строки
df_players = pd.read_csv(players_file, encoding="utf-8", on_bad_lines='skip')

# Убираем дубликаты по player_id
df_players = df_players.drop_duplicates(subset="player_id")

# Сохраняем чистый CSV
df_players.to_csv(players_clean_file, index=False, encoding="utf-8")
print(f"Готово! {players_clean_file} — без дубликатов и ошибок кодировки.")

