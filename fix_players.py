import pandas as pd

print("📊 Загружаем female_players_simple.csv...")
df = pd.read_csv('C:/Users/sbk/fifa/female_players_simple.csv', low_memory=False)

# 💰 Преобразуем числовые колонки (убираем .0)
for col in ['value_eur', 'wage_eur', 'team_id']:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

# 💾 Сохраняем новый исправленный файл
output_path = 'C:/Users/sbk/fifa/female_players_simple_fixed.csv'
df.to_csv(output_path, index=False)
print("✅ Исправленный файл создан:", output_path)
print("📈 Строк:", len(df))
