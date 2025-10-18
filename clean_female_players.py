import pandas as pd

# Загружаем CSV, пропуская строки с некорректной кодировкой
df = pd.read_csv(
    "female_players_simple_utf8.csv",
    encoding="utf-8",
    on_bad_lines='skip'  # пропускаем строки с битой кодировкой
)

# Сохраняем новый рабочий CSV
df.to_csv("female_players_simple_nodup_utf8.csv", index=False, encoding="utf-8")

print("Готово! Все строки с некорректной кодировкой пропущены.")

