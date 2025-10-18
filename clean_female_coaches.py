import pandas as pd

# Input / output files
coaches_file = "female_coaches.csv"
coaches_clean_file = "female_coaches_final_clean.csv"

# Load CSV as strings to catch all issues
df = pd.read_csv(coaches_file, dtype=str)

# Columns to check for bad characters
text_columns = ['coach_url', 'short_name', 'long_name', 'nationality_name', 'face_url']

# Function: returns True if the string contains only valid UTF-8 characters
def is_utf8_safe(s):
    if pd.isna(s):
        return True
    try:
        s.encode('utf-8')
        return True
    except UnicodeEncodeError:
        return False

# Keep only rows where all text columns are UTF-8 safe
mask = df[text_columns].applymap(is_utf8_safe).all(axis=1)

# Apply mask and drop duplicates by coach_id
df_clean = df[mask].drop_duplicates(subset="coach_id")

# Save the fully clean CSV
df_clean.to_csv(coaches_clean_file, index=False, encoding="utf-8")

print(f"Done! {coaches_clean_file} — no bad UTF-8 chars, no duplicates.")
