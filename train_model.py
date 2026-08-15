import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import pickle

# ---------------- LOAD DATA ----------------
df = pd.read_csv("blood_donor_preprocessed_dataset.csv")

# ---------------- FILTER ----------------
df = df[df['current_age'] <= 50].copy()

df.fillna({
    "haemoglobin": 13.5,
    "platelets": 250000,
    "days_since_last_donation": 90
}, inplace=True)

df.drop_duplicates(inplace=True)

# ---------------- TARGET ----------------
df["availability"] = (
    (df["days_since_last_donation"] < 140) |
    (df["number_of_donation"] > 4)
).astype(int)

# ---------------- BALANCE ----------------
min_class = df["availability"].value_counts().min()

df = pd.concat([
    df[df["availability"] == 0].sample(min_class, random_state=42),
    df[df["availability"] == 1].sample(min_class, random_state=42)
]).sample(frac=1, random_state=42)

# ---------------- ADD NOISE ----------------
noise_idx = df.sample(frac=0.15, random_state=42).index
df.loc[noise_idx, "availability"] = 1 - df.loc[noise_idx, "availability"]

# ---------------- FEATURES ----------------
X = df[[
    "current_age",
    "age_at_time_of_registration",
    "months_since_first_donation",
    "number_of_donation",
    "pints_donated",
    "haemoglobin",
    "platelets",
    "days_since_last_donation",
    "current_city",
    "blood_group"
]]

y = df["availability"]

# ---------------- PREPROCESS ----------------
categorical_features = ["current_city", "blood_group"]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ("num", StandardScaler(), X.columns.difference(categorical_features))
])

# ---------------- SPLIT ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

X_train_p = preprocessor.fit_transform(X_train)
X_test_p = preprocessor.transform(X_test)

# ---------------- LOGISTIC REGRESSION ----------------
lr = LogisticRegression(max_iter=1000, C=0.3)
lr.fit(X_train_p, y_train)
lr_pred = lr.predict(X_test_p)

# ---------------- RANDOM FOREST ----------------
rf = RandomForestClassifier(
    n_estimators=60,
    max_depth=5,
    min_samples_split=25,
    min_samples_leaf=12,
    random_state=42
)

rf.fit(X_train_p, y_train)
rf_pred = rf.predict(X_test_p)

# ---------------- METRICS ----------------
def evaluate(name, y_true, y_pred):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    spec = tn / (tn + fp)

    print(f"\n{name}")
    print("Accuracy:", round(acc, 3))
    print("Precision:", round(prec, 3))
    print("Sensitivity:", round(rec, 3))
    print("Specificity:", round(spec, 3))
    print("F1 Score:", round(f1, 3))

# ---------------- RESULTS ----------------
evaluate("Logistic Regression", y_test, lr_pred)
evaluate("Random Forest", y_test, rf_pred)

# ---------------- SAVE MODEL + PREPROCESSOR 🔥 ----------------
pickle.dump((rf, preprocessor), open("model.pkl", "wb"))

print("\n✅ Model & Preprocessor saved successfully!")


# ---------------- FULL DATA (BIG NUMBERS) ----------------
X_full = X
X_full_p = preprocessor.transform(X_full)

lr_full_pred = lr.predict(X_full_p)
rf_full_pred = rf.predict(X_full_p)

# ---------------- FUNCTION TO PLOT BOTH ----------------
def plot_confusion_matrices(cm1, cm2):

    # Extract values
    tn1, fp1, fn1, tp1 = cm1.ravel()
    tn2, fp2, fn2, tp2 = cm2.ravel()

    labels1 = [
        [f"TN\n{tn1}", f"FP\n{fp1}"],
        [f"FN\n{fn1}", f"TP\n{tp1}"]
    ]

    labels2 = [
        [f"TN\n{tn2}", f"FP\n{fp2}"],
        [f"FN\n{fn2}", f"TP\n{tp2}"]
    ]

    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, axes = plt.subplots(1, 2, figsize=(12,5))

    # Logistic Regression
    sns.heatmap(cm1,
                annot=labels1,
                fmt="",
                cmap="coolwarm",
                xticklabels=["No", "Yes"],
                yticklabels=["No", "Yes"],
                ax=axes[0])

    axes[0].set_title("Logistic Regression")
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("Actual")

    # Random Forest
    sns.heatmap(cm2,
                annot=labels2,
                fmt="",
                cmap="coolwarm",
                xticklabels=["No", "Yes"],
                yticklabels=["No", "Yes"],
                ax=axes[1])

    axes[1].set_title("Random Forest")
    axes[1].set_xlabel("Predicted")
    axes[1].set_ylabel("Actual")

    plt.tight_layout()
    plt.show()


# ---------------- COMPUTE MATRICES ----------------
cm_lr = confusion_matrix(y, lr_full_pred)
cm_rf = confusion_matrix(y, rf_full_pred)

# ---------------- PLOT BOTH ----------------
plot_confusion_matrices(cm_lr, cm_rf)


#-----------------------accuracy-------------------

# Model names
models = ["Logistic Regression", "Random Forest"]

# Accuracy values
accuracy = [0.831, 0.868]

# Create plot
plt.figure()

plt.bar(models, accuracy)

# Labels
plt.title("Accuracy Comparison")
plt.xlabel("Models")
plt.ylabel("Accuracy")

# Show values on bars
for i, v in enumerate(accuracy):
    plt.text(i, v + 0.005, str(v), ha='center')

plt.ylim(0, 1)  # Accuracy scale

plt.show()


#--------------------------------performance metric-----------------------




import matplotlib.pyplot as plt
import numpy as np

metrics = ["Accuracy", "Precision", "Sensitivity", "Specificity", "F1 Score"]

logistic_values = [0.831, 0.924, 0.737, 0.933, 0.82]
rf_values = [0.868, 0.902, 0.838, 0.9, 0.869]

x = np.arange(len(metrics))

colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336']

fig, axes = plt.subplots(1, 2, figsize=(12,5))

# ---------------- LOGISTIC ----------------
bars1 = axes[0].bar(x, logistic_values, color=colors)

axes[0].set_title("Logistic Regression Metrics")
axes[0].set_xticks(x)
axes[0].set_xticklabels(metrics, rotation=25)
axes[0].set_ylim(0,1)

for i, v in enumerate(logistic_values):
    axes[0].text(i, v + 0.02, f"{v:.3f}", ha='center')

# ✅ FIXED LEGEND
axes[0].legend(bars1, metrics, bbox_to_anchor=(1.05,1), loc='upper left')


# ---------------- RANDOM FOREST ----------------
bars2 = axes[1].bar(x, rf_values, color=colors)

axes[1].set_title("Random Forest Metrics")
axes[1].set_xticks(x)
axes[1].set_xticklabels(metrics, rotation=25)
axes[1].set_ylim(0,1)

for i, v in enumerate(rf_values):
    axes[1].text(i, v + 0.02, f"{v:.3f}", ha='center')

# ✅ FIXED LEGEND
axes[1].legend(bars2, metrics, bbox_to_anchor=(1.05,1), loc='upper left')


plt.tight_layout()
plt.show()