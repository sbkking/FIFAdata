import pandas as pd

print("📦 Проверяем файл female_players_simple_utf8.csv на дубликаты...")

df = pd.read_csv('C:/Users/Public/female_players_simple_utf8.csv', encoding='utf-8', low_memory=False)
dupes = df[df.duplicated(subset=['player_id'], keep=False)]

print("🔍 Найдено дубликатов:", len(dupes))

if len(dupes) > 0:
    print(dupes[['player_id', 'short_name', 'club_name']].head(10))
    # удалим дубликаты и сохраним новый файл
    df = df.drop_duplicates(subset=['player_id'])
    df.to_csv('C:/Users/Public/female_players_simple_nodup.csv', index=False, encoding='utf-8')
    print("✅ Создан новый файл без дубликатов: female_players_simple_nodup.csv")
else:
    print("✅ Дубликатов нет, всё чисто.")

