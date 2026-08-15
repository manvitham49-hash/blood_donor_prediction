import sys
import pandas as pd
import pickle

# -----------------------------
# Validate Input
# -----------------------------
if len(sys.argv) != 2:
    print("❌ Usage: python predict.py <donor_id>")
    sys.exit(1)

donor_id = sys.argv[1]

# -----------------------------
# Load Dataset
# -----------------------------
df = pd.read_csv("blood_donor_preprocessed_dataset.csv")

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# -----------------------------
# Find Donor
# -----------------------------
donor = df.loc[df["donor_id"] == donor_id]

if donor.empty:
    print("❌ Donor ID not found in dataset")
    sys.exit(1)

# -----------------------------
# Extract Details
# -----------------------------
name = donor["name"].values[0]
current_city = donor["current_city"].values[0]
blood_group = donor["blood_group"].values[0]

# -----------------------------
# Load Trained Model
# -----------------------------
model = pickle.load(open("model.pkl", "rb"))

# -----------------------------
# Prepare Features (IMPORTANT)
# Must match training features exactly
# -----------------------------
X = donor[[
    "current_city",
    "blood_group",
    "months_since_first_donation",
    "number_of_donation",
    "pints_donated"
]]

# -----------------------------
# Predict
# -----------------------------
probability = model.predict_proba(X)[:,1][0]
prediction = model.predict(X)[0]

# -----------------------------
# Output Result
# -----------------------------
print("----------- DONOR PREDICTION -----------")

print("Name:", name)
print("Current City:", current_city)
print("Blood Group:", blood_group)
print("Availability Probability:", round(float(probability),4))

if prediction == 1:
    print("🟢 Donor is LIKELY AVAILABLE for donation")
else:
    print("🔴 Donor is LIKELY UNAVAILABLE for donation")