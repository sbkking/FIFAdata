import pandas as pd

# 🧩 Нужные колонки из female_players.csv
cols = [
    'player_id','short_name','long_name','age','height_cm','weight_kg',
    'nationality_name','overall','potential','club_name','club_team_id',
    'player_positions','preferred_foot','weak_foot','skill_moves',
    'value_eur','wage_eur'
]

print("📊 Загружаем female_players.csv... (подожди немного)")
df = pd.read_csv('C:/Users/sbk/fifa/female_players.csv', usecols=cols, low_memory=False)

# Переименуем club_team_id → team_id для совместимости с таблицей
df.rename(columns={'club_team_id': 'team_id'}, inplace=True)

# 💾 Сохраняем облегчённую версию
output_path = 'C:/Users/sbk/fifa/female_players_simple.csv'
df.to_csv(output_path, index=False)

print("✅ Файл успешно создан:", output_path)
print("📈 Строк:", len(df))
print("📂 Колонки:", list(df.columns))
