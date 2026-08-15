import pandas as pd

df = pd.read_csv("blood_donor_preprocessed_dataset.csv", dtype=str)  # 🔴 FORCE STRING

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# 🔴 Replace ALL possible values
df["donor_details_updated_by_admin"] = (
    df["donor_details_updated_by_admin"]
    .astype(str)
    .str.strip()
    .replace({
        "True": "Yes",
        "False": "No",
        "TRUE": "Yes",
        "FALSE": "No",
        "Yes": "Yes",
        "No": "No"
    })
)

df.to_csv("blood_donor_dataset.csv", index=False)

print("Fixed TRUE → Yes ✅")