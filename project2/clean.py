import pandas as pd
import numpy as np

# ----------------------------------------
# 1. LOAD THE EXCEL FILE
# ----------------------------------------

file_path = "Historical_Stock_Market_Data_Cleaning_Practice(1).xlsx"

try:
    df = pd.read_excel(
        file_path,
        sheet_name="Raw_Market_Data"
    )
except ValueError:
    # fallback to first sheet if the expected sheet name is not present
    print("Worksheet 'Raw_Market_Data' not found — falling back to the first sheet.")
    df = pd.read_excel(file_path, sheet_name=0)

print("Original data:")
print(df.head())
print("\nOriginal shape:", df.shape)


# ----------------------------------------
# 2. CLEAN COLUMN NAMES
# ----------------------------------------

df.columns = df.columns.str.strip()

print("\nColumns:")
print(df.columns.tolist())


# ----------------------------------------
# 3. CONVERT DATA TYPES
# ----------------------------------------

# Convert Date to datetime
df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

# Convert financial columns to numbers
numeric_columns = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ----------------------------------------
# 4. CHECK MISSING VALUES
# ----------------------------------------

print("\nMissing values before cleaning:")
print(df.isnull().sum())


# ----------------------------------------
# 5. FIND DUPLICATES
# ----------------------------------------

print("\nDuplicate records:")

duplicates = df[
    df.duplicated(
        subset=["Date", "Ticker"],
        keep=False
    )
]

print(duplicates)


# Remove duplicate Date + Ticker records
df = df.drop_duplicates(
    subset=["Date", "Ticker"],
    keep="first"
)


# ----------------------------------------
# 6. CHECK INVALID OHLC DATA
# ----------------------------------------

# High cannot be lower than Open or Close
invalid_high = (
    (df["High"] < df["Open"]) |
    (df["High"] < df["Close"])
)

# Low cannot be higher than Open or Close
invalid_low = (
    (df["Low"] > df["Open"]) |
    (df["Low"] > df["Close"])
)

# High cannot be lower than Low
invalid_high_low = (
    df["High"] < df["Low"]
)

invalid_ohlc = (
    invalid_high |
    invalid_low |
    invalid_high_low
)

print("\nInvalid OHLC records:")
print(df[invalid_ohlc])


# ----------------------------------------
# 7. CHECK NEGATIVE VOLUME
# ----------------------------------------

negative_volume = df["Volume"] < 0

print("\nNegative volume records:")
print(df[negative_volume])


# Replace negative volume with NaN
df.loc[negative_volume, "Volume"] = np.nan


# ----------------------------------------
# 8. CHECK INVALID PRICES
# ----------------------------------------

invalid_price = (
    (df["Open"] <= 0) |
    (df["High"] <= 0) |
    (df["Low"] <= 0) |
    (df["Close"] <= 0)
)

print("\nInvalid price records:")
print(df[invalid_price])


# Replace invalid prices with NaN
price_columns = [
    "Open",
    "High",
    "Low",
    "Close"
]

for column in price_columns:
    df.loc[df[column] <= 0, column] = np.nan


# ----------------------------------------
# 9. SORT DATA
# ----------------------------------------

df = df.sort_values(
    ["Ticker", "Date"]
).reset_index(drop=True)


# ----------------------------------------
# 10. CALCULATE DAILY RETURNS
# ----------------------------------------

df["Daily_Return"] = (
    df.groupby("Ticker")["Close"]
    .pct_change()
)


# ----------------------------------------
# 11. DETECT ABNORMAL PRICE MOVEMENTS
# ----------------------------------------

# Flag movements greater than 10%
abnormal_return = (
    df["Daily_Return"].abs() > 0.10
)

df["Abnormal_Return_Flag"] = abnormal_return

print("\nAbnormal price movements:")
print(
    df[abnormal_return][
        [
            "Date",
            "Ticker",
            "Close",
            "Daily_Return"
        ]
    ]
)


# ----------------------------------------
# 12. CREATE DATA QUALITY FLAGS
# ----------------------------------------

df["Missing_Data_Flag"] = (
    df.isnull().any(axis=1)
)

df["Invalid_OHLC_Flag"] = invalid_ohlc

df["Negative_Volume_Flag"] = (
    df["Volume"] < 0
)

df["Invalid_Price_Flag"] = (
    (df["Open"] <= 0) |
    (df["High"] <= 0) |
    (df["Low"] <= 0) |
    (df["Close"] <= 0)
)

df["Any_Issue"] = (
    df["Missing_Data_Flag"] |
    df["Invalid_OHLC_Flag"] |
    df["Abnormal_Return_Flag"]
)


# ----------------------------------------
# 13. HANDLE MISSING VALUES
# ----------------------------------------

# For this practice project, use forward fill
# within each ticker for missing market values.

df[price_columns] = (
    df.groupby("Ticker")[price_columns]
    .ffill()
)

df["Volume"] = (
    df.groupby("Ticker")["Volume"]
    .ffill()
)


# ----------------------------------------
# 14. RECHECK MISSING VALUES
# ----------------------------------------

print("\nMissing values after cleaning:")
print(df.isnull().sum())


# ----------------------------------------
# 15. CREATE A QUALITY SUMMARY
# ----------------------------------------

quality_summary = pd.DataFrame({
    "Metric": [
        "Original Rows",
        "Final Rows",
        "Duplicate Records",
        "Missing Values",
        "Invalid OHLC Records",
        "Abnormal Price Movements"
    ],
    "Count": [
        500,
        len(df),
        len(duplicates),
        df.isnull().sum().sum(),
        invalid_ohlc.sum(),
        abnormal_return.sum()
    ]
})

print("\nQuality Summary:")
print(quality_summary)


# ----------------------------------------
# 16. SAVE CLEANED DATA
# ----------------------------------------

output_file = "Cleaned_Stock_Market_Data.xlsx"

with pd.ExcelWriter(
    output_file,
    engine="openpyxl"
) as writer:

    df.to_excel(
        writer,
        sheet_name="Cleaned_Data",
        index=False
    )

    quality_summary.to_excel(
        writer,
        sheet_name="Quality_Summary",
        index=False
    )

    df[df["Any_Issue"]].to_excel(
        writer,
        sheet_name="Flagged_Records",
        index=False
    )


print("\n----------------------------------------")
print("Cleaning completed successfully!")
print("Saved as:", output_file)
print("----------------------------------------")
