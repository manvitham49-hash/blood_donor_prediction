import pandas as pd

df = pd.read_csv("blood_donor_preprocessed_dataset.csv")

for i, row in df.iterrows():
    print(i, row["donor_id"], row["name"], row["email"])
