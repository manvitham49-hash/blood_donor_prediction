import pandas as pd

# ---------------- LOAD DATA ----------------
df = pd.read_csv("blood_donor_dataset.csv")

print("Before processing:", df.shape)

# ---------------- STEP 1: FILTER AGE ----------------
df = df[df['current_age'] <= 50].copy()   # 🔥 avoids warnings

# ---------------- STEP 2: HANDLE MISSING VALUES ----------------

# Fill numeric columns with median
numeric_cols = df.select_dtypes(include=['number']).columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

# Fill categorical columns with mode
categorical_cols = df.select_dtypes(include=['object']).columns
for col in categorical_cols:
    df[col] = df[col].fillna(df[col].mode()[0])

# ---------------- STEP 3: REMOVE DUPLICATES ----------------
df = df.drop_duplicates()

print("After processing:", df.shape)

# ---------------- SAVE FILE ----------------
df.to_csv("blood_donor_preprocessed_dataset.csv", index=False)

print("✅ Preprocessing completed and saved as 'blood_donor_preprocessed_dataset.csv'")