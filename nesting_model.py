import pandas as pd
import numpy as np
from datetime import datetime, time

from statsmodels.tools import add_constant
from statsmodels.discrete.discrete_model import Logit
from statsmodels.genmod.families import NegativeBinomial

### Manual AUC Function (no sklearn)
def compute_auc(y_true, y_prob):
    data = pd.DataFrame({"y": y_true, "p": y_prob})
    data = data.sort_values("p")

    cum_pos = (data["y"] == 1).cumsum()
    total_pos = (data["y"] == 1).sum()
    total_neg = (data["y"] == 0).sum()

    auc = cum_pos[data["y"] == 0].sum() / (total_pos * total_neg)
    return auc

# 1. Load Data
df = pd.read_csv("filenmae.csv")
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").reset_index(drop=True)

# 2. Feature Engineering
# 2.a. Seasonal Terms
df["DayOfSeason"] = (df["Date"] - df["Date"].min()).dt.days + 1
df["DayOfSeason1"] = df["DayOfSeason"] ** 2

# 2.b. Tide Variables
df["TideRange"] = df["HighTideHeight"] - df["LowTideHeight"]

def time_to_minutes(t):
    t = pd.to_datetime(t, format="%H%M").time()
    return t.hour * 60 + t.minute

df["HighTideMinutes"] = df["HighTideTime"].apply(time_to_minutes)
patrol_start = 19 * 60
df["TimeFromHighTide"] = abs(df["HighTideMinutes"] - patrol_start)

# 2.c. Luna Cyclical Encoding
moon_map = {
    "Luna nueva": 0,
    "Luna creciente": 1,
    "Cuarto creciente": 2,
    "Gibosa creciente": 3,
    "Luna llena": 4,
    "Gibosa menguante": 5,
    "Cuarto menguante": 6,
    "Luna menguante": 7
}

df["MoonNum"] = df["LunarPhase"].map(moon_map)

df["Moon_sin"] = np.sin(2 * np.pi * df["MoonNum"] / 8)
df["Moon_cos"] = np.cos(2 * np.pi * df["MoonNum"] / 8)

# 3. Negative Binomial Model (Daily Nest Count)
df_model = df.dropna(subset=["TotalNests"])

predictors = [
    "HighTideHeight",
    "TideRange",
    "TimeFromHighTide",
    "Moon_sin",
    "Moon_cos",
    "DayOfSeason",
    "DayOfSeason2"
]

x = add_constant(df_model[predictors])
y = df_model["TotalNests"]

nb_model = sm.GLM(
    y,
    x,
    family=NegativeBinomial()
).fit()

print(nb_model.summary())

# 3.a. Incident Rate Ratios
irr = np.exp(nb_model.params)
print("\nIncident Rate Ratios:")
print(irr)

# 4. Define High Nesting Event (Top 25%)
threshold = df_model["TotalNests"].quantile(0.75)
df_model["HighEvent"] = (df_model["TotalNests"] >= threshold).astype(int)

# 5. Train/Test Split (Manual, Time-Based)
train = df_model[df_model["Date"] < "2025-12-11"]
test = df_model[df_model["Date"] >= "2025-12-11"]

# 6. Logistic Model (statsmodel Logit)
x_train = add_constant(train[predictors])
y_train = train["HighEvent"]

log_model = Logit(y_train, x_train).fit()

print(log_model.summary())

# 6.a. Odds Ratios
odds_ratios = np.exp(log_model.params)
print("\nOdds Ratios:")
print(odds_ratios)

# 7. Test Performance
x_test = add_constant(test[predictors])
y_test = test["HighEvent"]

y_prob = log_model.predict(x_test)
y_pred = (y_prob > 0.5).astype(int)

accuracy = (y_pred == y_test).mean()
auc = compute_auc(y_test.values, y_prob.values)

print("\nTest Accuracy:", accuracy)
print("Test AUC:", auc)

