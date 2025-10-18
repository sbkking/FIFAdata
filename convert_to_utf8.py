import pandas as pd

print("📦 Читаем female_players_simple_fixed.csv с автоопределением кодировки...")

# Попробуем открыть в универсальной кодировке latin1 (все байты читаются)
df = pd.read_csv('C:/Users/sbk/fifa/female_players_simple_fixed.csv', encoding='latin1', low_memory=False)

# 💾 Сохраняем в правильной UTF-8
output_path = 'C:/Users/sbk/fifa/female_players_simple_utf8.csv'
df.to_csv(output_path, index=False, encoding='utf-8')

print("✅ Файл перекодирован в UTF-8 и сохранён как:")
print(output_path)
print("📈 Строк:", len(df))
