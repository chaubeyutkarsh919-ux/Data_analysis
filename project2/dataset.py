import pandas as pd
import numpy as np

np.random.seed(42)

# -----------------------------------------
# CREATE 60 BUSINESS DAYS
# -----------------------------------------

dates = pd.bdate_range(
    start="2025-01-01",
    periods=60
)

n = len(dates)

# -----------------------------------------
# CREATE STOCK PRICES
# -----------------------------------------

close_prices = np.cumsum(
    np.random.normal(0.5, 2, n)
) + 100

data = pd.DataFrame({
    "Date": dates,
    "Ticker": ["AAPL"] * n,
    "Open": close_prices + np.random.normal(0, 1, n),
    "High": close_prices + np.random.uniform(0.5, 3, n),
    "Low": close_prices - np.random.uniform(0.5, 3, n),
    "Close": close_prices,
    "Volume": np.random.randint(
        100000,
        1000000,
        n
    )
})

# -----------------------------------------
# INTRODUCE DATA QUALITY PROBLEMS
# -----------------------------------------

# 1. Missing Close
data.loc[5, "Close"] = np.nan

# 2. Missing Volume
data.loc[12, "Volume"] = np.nan

# 3. Missing Open
data.loc[20, "Open"] = np.nan

# 4. Duplicate rows
data = pd.concat(
    [data, data.iloc[[10, 15]]],
    ignore_index=True
)

# 5. Negative volume
data.loc[25, "Volume"] = -50000

# 6. Invalid High/Low relationship
data.loc[30, "High"] = data.loc[30, "Low"] - 5

# 7. Open greater than High
data.loc[35, "Open"] = data.loc[35, "High"] + 10

# 8. Close lower than Low
data.loc[40, "Close"] = data.loc[40, "Low"] - 20

# 9. Abnormal price movement
data.loc[45, "Close"] = data.loc[45, "Close"] * 2.5

# 10. Text in Volume
data["Volume"] = data["Volume"].astype(object)
data.loc[50, "Volume"] = "unknown"

# 11. Invalid Date
data["Date"] = data["Date"].astype(object)
data.loc[52, "Date"] = "not_a_date"

# 12. Missing Date
data.loc[55, "Date"] = np.nan

# -----------------------------------------
# SAVE DATASET
# -----------------------------------------

data.to_excel(
    "Historical_Stock_Market_Data_Messy.xlsx",
    index=False
)

print("Messy dataset created successfully!")

print("\nDataset shape:")
print(data.shape)

print("\nData types:")
print(data.dtypes)

print("\nFirst 10 rows:")
print(data.head(10))