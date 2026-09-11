

import os
import re
import numpy as np
import pandas as pd


# -----------------------------------------------------------------------------
# 1. HELPER PARSING FUNCTIONS
# -----------------------------------------------------------------------------

def clean_financial_number(val) -> float:
    """
    Parses messy financial currency/numeric strings into clean floats.
    Handles:
      - Accounting negatives in parentheses: '(125,000.00)', '($12.4M)'
      - Currency symbols & text: '$', 'USD', 'US$', '€', 'CAD'
      - Multipliers: 'B' (billion), 'M' (million), 'K' (thousand)
      - Commas and extra whitespace: ' 1,234,567.89 '
      - Sentinels & errors: '#VALUE!', 'N/A', 'None', '-', 'null', ''
    """
    if pd.isna(val):
        return np.nan

    val_str = str(val).strip()
    if not val_str:
        return np.nan

    # Check known sentinels
    upper_val = val_str.upper()
    sentinels = {"N/A", "NA", "NONE", "NULL", "-", "#VALUE!", "#DIV/0!", "ERROR", "TBD", "MISSING", "?"}
    if upper_val in sentinels:
        return np.nan

    is_negative = False

    # Check accounting parentheses: '( ... )'
    if val_str.startswith("(") and val_str.endswith(")"):
        is_negative = True
        val_str = val_str[1:-1].strip()
    elif val_str.startswith("-"):
        is_negative = True
        val_str = val_str[1:].strip()
    elif "-$" in val_str or "- $" in val_str:
        is_negative = True
        val_str = val_str.replace("-$", "").replace("- $", "").strip()

    # Strip currency prefixes and letters
    for prefix in ["US$", "USD", "US $", "$", "€", "£", "CAD"]:
        val_str = val_str.replace(prefix, "").strip()

    # Check multipliers (B, M, K)
    multiplier = 1.0
    if val_str.upper().endswith("B"):
        multiplier = 1e9
        val_str = val_str[:-1].strip()
    elif val_str.upper().endswith("M"):
        multiplier = 1e6
        val_str = val_str[:-1].strip()
    elif val_str.upper().endswith("K"):
        multiplier = 1e3
        val_str = val_str[:-1].strip()

    # Remove commas & whitespace
    val_str = val_str.replace(",", "").strip()

    try:
        num = float(val_str) * multiplier
        return -num if is_negative else num
    except (ValueError, TypeError):
        return np.nan


def clean_eps(val) -> float:
    """
    Parses messy EPS values.
    Handles currency signs, accounting brackets, and error tokens.
    """
    if pd.isna(val):
        return np.nan

    val_str = str(val).strip()
    if not val_str:
        return np.nan

    upper_val = val_str.upper()
    if upper_val in {"N/A", "NA", "NONE", "NULL", "-", "ERROR", "#DIV/0!", "#VALUE!", "TBD"}:
        return np.nan

    is_negative = False
    if val_str.startswith("(") and val_str.endswith(")"):
        is_negative = True
        val_str = val_str[1:-1].strip()
    elif val_str.startswith("-"):
        is_negative = True
        val_str = val_str[1:].strip()
    elif "-$" in val_str or "- $" in val_str:
        is_negative = True
        val_str = val_str.replace("-$", "").replace("- $", "").strip()

    for prefix in ["US$", "USD", "$"]:
        val_str = val_str.replace(prefix, "").strip()

    val_str = val_str.replace(",", "").strip()

    try:
        num = float(val_str)
        return -num if is_negative else num
    except (ValueError, TypeError):
        return np.nan


def clean_margin(val) -> float:
    """
    Parses messy margin strings into standard decimal proportions (e.g. 0.155 for 15.5%).
    Handles:
      - Percent signs: '15.5%', '(2.9%)', '-9.36%'
      - Accounting negative parentheses: '(2.9%)' -> -0.029
      - Decimal vs whole percentage point scale harmonization
      - Sentinel strings and formula errors
    """
    if pd.isna(val):
        return np.nan

    val_str = str(val).strip()
    if not val_str:
        return np.nan

    upper_val = val_str.upper()
    if upper_val in {"N/A", "NA", "NONE", "NULL", "-", "#DIV/0!", "#VALUE!", "ERROR", "TBD"}:
        return np.nan

    is_negative = False
    if val_str.startswith("(") and val_str.endswith(")"):
        is_negative = True
        val_str = val_str[1:-1].strip()
    elif val_str.startswith("-"):
        is_negative = True
        val_str = val_str[1:].strip()

    has_pct_symbol = "%" in val_str
    val_str = val_str.replace("%", "").replace(",", "").strip()

    try:
        num = float(val_str)
        if is_negative:
            num = -abs(num)

        # Scale harmonization:
        # If it had '%', divide by 100 (e.g. 15.5% -> 0.155)
        # If no '%', but abs(num) > 1.0 (e.g. '5.38' or '45.49'), it was recorded in percentage points
        # If abs(num) <= 1.0 (e.g. '0.0606'), it was already recorded as a decimal ratio
        if has_pct_symbol:
            return round(num / 100.0, 6)
        elif abs(num) > 1.0:
            return round(num / 100.0, 6)
        else:
            return round(num, 6)
    except (ValueError, TypeError):
        return np.nan


def parse_reporting_date(date_val):
    """
    Parses heterogeneous date formats into standard datetime:
      - '2022/09/30', '09/30/2024', '30-06-2022', '2021-12-31'
      - 'FY2022', 'FY22'
      - 'Q1 2022', 'Q2 2022', 'Q3 2022', 'Q4 2022'
      - '2023'
    """
    if pd.isna(date_val):
        return pd.NaT

    d_str = str(date_val).strip()
    if not d_str:
        return pd.NaT

    # Fiscal Year string: FY2022 or FY22
    fy_match = re.match(r"^FY\s*(\d{2,4})$", d_str, re.IGNORECASE)
    if fy_match:
        yr = int(fy_match.group(1))
        yr = 2000 + yr if yr < 100 else yr
        return pd.Timestamp(year=yr, month=12, day=31)

    # Quarter string: Q1 2022, Q2 2023
    q_match = re.match(r"^Q([1-4])\s*[-/]?\s*(\d{4})$", d_str, re.IGNORECASE)
    if q_match:
        q = int(q_match.group(1))
        yr = int(q_match.group(2))
        q_month_end = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
        m, d = q_month_end[q]
        return pd.Timestamp(year=yr, month=m, day=d)

    # Just 4-digit year: 2023
    if re.match(r"^\d{4}$", d_str):
        return pd.Timestamp(year=int(d_str), month=12, day=31)

    # Standard flexible date parsing
    try:
        return pd.to_datetime(d_str, format="mixed", dayfirst=False)
    except Exception:
        try:
            return pd.to_datetime(d_str, dayfirst=True)
        except Exception:
            return pd.NaT


# -----------------------------------------------------------------------------
# 2. MAIN CLEANING PIPELINE
# -----------------------------------------------------------------------------

def clean_financial_dataset(input_csv_path: str, output_csv_path: str):


    # 1. LOAD THE DATA
    print(f"\n[Step 1] Loading raw dataset from: {input_csv_path}")
    df_raw = pd.read_csv(input_csv_path, dtype=str)
    original_row_count = len(df_raw)
    print(f"Loaded {original_row_count} rows across {len(df_raw.columns)} columns.")

    df = df_raw.copy()

    # 2. CLEAN COLUMN NAMES
    print("\n[Step 2] Cleaning column names...")
    df.columns = df.columns.str.strip()
    print("Columns:", df.columns.tolist())

    # 3. DETECT & REMOVE DUPLICATE RECORDS
    print("\n[Step 3] Checking for duplicate records...")
    exact_duplicates = df.duplicated().sum()
    print(f"Exact duplicate rows detected: {exact_duplicates}")
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    print(f"Rows remaining after deduplication: {len(df)}")

    # 4. STANDARDIZE IDENTIFIERS (Company_ID, Ticker, Company_Name)
    print("\n[Step 4] Standardizing company identifiers...")

    # Standardize Company_ID format (ensure CMP-XXXX)
    df["Company_ID"] = df["Company_ID"].astype(str).str.strip()
    df["Company_ID"] = df["Company_ID"].apply(
        lambda x: re.sub(r"^CMP(\d+)$", r"CMP-\1", x) if re.match(r"^CMP\d+$", x) else x
    )

    # Standardize Ticker
    df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
    df["Ticker"] = df["Ticker"].replace({"NAN": np.nan, "NONE": np.nan, "": np.nan})

    # Standardize Company_Name
    df["Company_Name"] = df["Company_Name"].astype(str).str.strip()
    df["Company_Name"] = df["Company_Name"].replace({"nan": np.nan, "None": np.nan, "": np.nan})
    # Title-case company names while preserving known acronyms
    df["Company_Name"] = df["Company_Name"].apply(
        lambda x: " ".join([w.upper() if w.upper() in ["AI", "IT", "II", "III", "IV"] else w.capitalize() for w in x.split()]) if pd.notna(x) else x
    )

    # 5. HARMONIZE SECTOR & IMPUTE MISSING SECTORS
    print("\n[Step 5] Harmonizing sector classifications...")

    sector_clean_map = {
        "TECHNOLOGY": "Technology",
        "TECH": "Technology",
        "INFORMATION TECHNOLOGY": "Technology",
        "IT": "Technology",
        "FINANCIAL SERVICES": "Financial Services",
        "FINANCIALS": "Financial Services",
        "FINANCE": "Financial Services",
        "FIN SERVICES": "Financial Services",
        "BANKING & FINANCE": "Financial Services",
        "HEALTHCARE": "Healthcare",
        "HEALTH CARE": "Healthcare",
        "BIO/PHARMA": "Healthcare",
        "CONSUMER CYCLICAL": "Consumer Cyclical",
        "CONSUMER DISCRETIONARY": "Consumer Cyclical",
        "CONS. CYCLICAL": "Consumer Cyclical",
        "RETAIL & CONSUMER": "Consumer Cyclical",
        "ENERGY": "Energy",
        "ENERGY & POWER": "Energy",
        "OIL & GAS": "Energy",
        "ENRGY": "Energy",
        "INDUSTRIALS": "Industrials",
        "INDUSTRIAL": "Industrials",
        "MANUFACTURING": "Industrials",
        "IND.": "Industrials",
    }

    # Normalize sector string
    norm_sector = df["Sector"].astype(str).str.strip().str.upper()
    df["Sector"] = norm_sector.map(sector_clean_map)

    # Build Company -> Sector lookup from known rows to impute missing / unknown sectors
    known_company_sectors = (
        df.dropna(subset=["Company_Name", "Sector"])
        .groupby("Company_Name")["Sector"]
        .agg(lambda s: s.mode()[0] if not s.empty else np.nan)
        .to_dict()
    )

    # Impute missing sectors from known companies
    missing_sectors_before = df["Sector"].isna().sum()
    df["Sector"] = df["Sector"].fillna(df["Company_Name"].map(known_company_sectors))
    # Fallback to Ticker if company name wasn't mapped
    known_ticker_sectors = (
        df.dropna(subset=["Ticker", "Sector"])
        .groupby("Ticker")["Sector"]
        .agg(lambda s: s.mode()[0] if not s.empty else np.nan)
        .to_dict()
    )
    df["Sector"] = df["Sector"].fillna(df["Ticker"].map(known_ticker_sectors))
    df["Sector"] = df["Sector"].fillna("Unclassified")
    imputed_sectors = missing_sectors_before - (df["Sector"] == "Unclassified").sum()
    print(f"Harmonized sectors. Imputed {imputed_sectors} previously missing sector tags.")

    # 6. STANDARDIZE CURRENCY
    print("\n[Step 6] Standardizing reporting currency...")
    df["Currency"] = df["Currency"].astype(str).str.strip().str.upper()
    df["Currency"] = df["Currency"].replace({"$": "USD", "US$": "USD", "NAN": "USD", "NONE": "USD", "-": "USD", "": "USD"})
    valid_currencies = {"USD", "EUR", "CAD", "GBP", "JPY"}
    df["Currency"] = df["Currency"].apply(lambda c: c if c in valid_currencies else "USD")

    # 7. PARSE REPORTING PERIOD DATES & FISCAL YEAR
    print("\n[Step 7] Parsing reporting dates & extracting Fiscal Year...")
    df["Reporting_Date"] = df["Reporting_Period"].apply(parse_reporting_date)
    df["Fiscal_Year"] = df["Reporting_Date"].dt.year
    # Fallback: if date parsing failed, extract 4-digit year from string
    df["Fiscal_Year"] = df["Fiscal_Year"].fillna(
        df["Reporting_Period"].astype(str).str.extract(r"(\d{4})")[0].astype(float)
    )

    # 8. PARSE FINANCIAL NUMERICS (Revenue, Operating_Profit, Net_Income)
    print("\n[Step 8] Parsing numeric financial metrics (Revenue, Operating Profit, Net Income)...")
    df["Revenue_Clean"] = df["Revenue"].apply(clean_financial_number)
    df["Operating_Profit_Clean"] = df["Operating_Profit"].apply(clean_financial_number)
    df["Net_Income_Clean"] = df["Net_Income"].apply(clean_financial_number)

    # 9. PARSE EPS & DETECT FAT-FINGER OUTLIERS
    print("\n[Step 9] Parsing EPS and detecting extreme outliers...")
    df["EPS_Clean"] = df["EPS"].apply(clean_eps)

    # Flag and handle EPS outliers (> $100/share or < -$50/share are typical fat-finger / data-entry glitches)
    eps_outliers = (df["EPS_Clean"].abs() > 100)
    print(f"Extreme EPS outliers detected (> $100/share): {eps_outliers.sum()}")
    df["EPS_Outlier_Flag"] = eps_outliers
    df.loc[eps_outliers, "EPS_Clean"] = np.nan  # Set corrupt outliers to NaN for imputation / safe aggregation

    # 10. PARSE PROFIT MARGINS
    print("\n[Step 10] Parsing profit margins and standardizing to decimal ratio...")
    df["Operating_Margin_Clean"] = df["Operating_Margin"].apply(clean_margin)
    df["Net_Profit_Margin_Clean"] = df["Net_Profit_Margin"].apply(clean_margin)

    # Flag extreme margin outliers (margins > 100% or < -100%)
    op_margin_outliers = (df["Operating_Margin_Clean"].abs() > 1.0)
    net_margin_outliers = (df["Net_Profit_Margin_Clean"].abs() > 1.0)
    df.loc[op_margin_outliers, "Operating_Margin_Clean"] = np.nan
    df.loc[net_margin_outliers, "Net_Profit_Margin_Clean"] = np.nan

    # 11. FINANCIAL CONSISTENCY CHECKS & IMPUTATION VIA ACCOUNTING IDENTITIES
    print("\n[Step 11] Validating financial accounting identities & imputing missing values...")

    # Identity 1: Operating Margin = Operating Profit / Revenue
    # If Margin is missing but Profit and Revenue exist, calculate it
    can_calc_op_margin = df["Operating_Margin_Clean"].isna() & df["Operating_Profit_Clean"].notna() & (df["Revenue_Clean"] > 0)
    df.loc[can_calc_op_margin, "Operating_Margin_Clean"] = (
        df.loc[can_calc_op_margin, "Operating_Profit_Clean"] / df.loc[can_calc_op_margin, "Revenue_Clean"]
    ).round(6)

    # If Operating Profit is missing but Margin and Revenue exist, recalculate Operating Profit
    can_calc_op_profit = df["Operating_Profit_Clean"].isna() & df["Operating_Margin_Clean"].notna() & df["Revenue_Clean"].notna()
    df.loc[can_calc_op_profit, "Operating_Profit_Clean"] = (
        df.loc[can_calc_op_profit, "Revenue_Clean"] * df.loc[can_calc_op_profit, "Operating_Margin_Clean"]
    ).round(2)

    # Identity 2: Net Profit Margin = Net Income / Revenue
    can_calc_net_margin = df["Net_Profit_Margin_Clean"].isna() & df["Net_Income_Clean"].notna() & (df["Revenue_Clean"] > 0)
    df.loc[can_calc_net_margin, "Net_Profit_Margin_Clean"] = (
        df.loc[can_calc_net_margin, "Net_Income_Clean"] / df.loc[can_calc_net_margin, "Revenue_Clean"]
    ).round(6)

    # If Net Income is missing but Net Margin and Revenue exist, recalculate Net Income
    can_calc_net_income = df["Net_Income_Clean"].isna() & df["Net_Profit_Margin_Clean"].notna() & df["Revenue_Clean"].notna()
    df.loc[can_calc_net_income, "Net_Income_Clean"] = (
        df.loc[can_calc_net_income, "Revenue_Clean"] * df.loc[can_calc_net_income, "Net_Profit_Margin_Clean"]
    ).round(2)

    # Impute missing Revenue if both Operating Profit and Operating Margin are available
    can_calc_rev = df["Revenue_Clean"].isna() & df["Operating_Profit_Clean"].notna() & (df["Operating_Margin_Clean"].abs() > 0.001)
    df.loc[can_calc_rev, "Revenue_Clean"] = (
        df.loc[can_calc_rev, "Operating_Profit_Clean"] / df.loc[can_calc_rev, "Operating_Margin_Clean"]
    ).round(2)

    # 12. FINANCIAL LOGIC CHECKS & ANOMALY FLAGS
    print("\n[Step 12] Creating analytical flags for data quality & audit...")

    # Contradiction Flag: Net Income > Revenue (accounting anomaly / error)
    net_income_gt_revenue = (
        (df["Net_Income_Clean"] > df["Revenue_Clean"]) &
        (df["Revenue_Clean"] > 0) &
        (df["Net_Income_Clean"].notna())
    )
    df["Anomaly_Net_Income_Exceeds_Revenue"] = net_income_gt_revenue

    # Operating Loss Flag
    df["Operating_Loss_Flag"] = df["Operating_Profit_Clean"] < 0

    # Net Loss Flag
    df["Net_Loss_Flag"] = df["Net_Income_Clean"] < 0

    # Missing critical data flag
    df["Missing_Data_Flag"] = (
        df[["Revenue_Clean", "Operating_Profit_Clean", "Net_Income_Clean", "EPS_Clean"]].isna().any(axis=1)
    )

    # Create percentage display columns for convenience (e.g. 15.4%)
    df["Operating_Margin_Pct"] = (df["Operating_Margin_Clean"] * 100.0).round(2)
    df["Net_Profit_Margin_Pct"] = (df["Net_Profit_Margin_Clean"] * 100.0).round(2)

    # Organize clean DataFrame schema
    clean_columns_order = [
        "Company_ID",
        "Ticker",
        "Company_Name",
        "Sector",
        "Fiscal_Year",
        "Reporting_Date",
        "Currency",
        "Revenue_Clean",
        "Operating_Profit_Clean",
        "Net_Income_Clean",
        "EPS_Clean",
        "Operating_Margin_Clean",
        "Operating_Margin_Pct",
        "Net_Profit_Margin_Clean",
        "Net_Profit_Margin_Pct",
        "Operating_Loss_Flag",
        "Net_Loss_Flag",
        "EPS_Outlier_Flag",
        "Anomaly_Net_Income_Exceeds_Revenue",
        "Missing_Data_Flag"
    ]

    df_cleaned = df[clean_columns_order].copy()
    df_cleaned = df_cleaned.rename(columns={
        "Revenue_Clean": "Revenue",
        "Operating_Profit_Clean": "Operating_Profit",
        "Net_Income_Clean": "Net_Income",
        "EPS_Clean": "EPS",
        "Operating_Margin_Clean": "Operating_Margin",
        "Net_Profit_Margin_Clean": "Net_Profit_Margin"
    })

    # Sort logically by Sector, Company_Name, Fiscal_Year
    df_cleaned = df_cleaned.sort_values(
        by=["Sector", "Company_Name", "Fiscal_Year"],
        na_position="last"
    ).reset_index(drop=True)

    # 13. GENERATE AUDIT & QUALITY SUMMARY
    print("\n[Step 13] Compiling Data Quality Summary...")
    quality_metrics = [
        ("Original Row Count", original_row_count),
        ("Duplicates Removed", exact_duplicates),
        ("Final Cleaned Row Count", len(df_cleaned)),
        ("Missing Revenue Remaining", df_cleaned["Revenue"].isna().sum()),
        ("Missing Operating Profit Remaining", df_cleaned["Operating_Profit"].isna().sum()),
        ("Missing Net Income Remaining", df_cleaned["Net_Income"].isna().sum()),
        ("Missing EPS Remaining", df_cleaned["EPS"].isna().sum()),
        ("EPS Outliers Corrected/Flagged", df["EPS_Outlier_Flag"].sum()),
        ("Accounting Anomaly (Net Income > Rev)", df_cleaned["Anomaly_Net_Income_Exceeds_Revenue"].sum()),
        ("Companies Operating at Loss", df_cleaned["Operating_Loss_Flag"].sum()),
        ("Companies with Net Loss", df_cleaned["Net_Loss_Flag"].sum()),
    ]
    df_quality_summary = pd.DataFrame(quality_metrics, columns=["Audit_Metric", "Count"])
    print(df_quality_summary.to_string(index=False))

    # 14. GENERATE CROSS-SECTOR BENCHMARK SUMMARY (The Investment Firm's Business Objective)
    print("\n[Step 14] Calculating cross-sector comparative performance benchmarks...")
    valid_data = df_cleaned[~df_cleaned["Anomaly_Net_Income_Exceeds_Revenue"]]

    sector_benchmark = (
        valid_data.groupby("Sector")
        .agg(
            Company_Count=("Company_ID", "count"),
            Avg_Revenue_USD=("Revenue", "mean"),
            Median_Revenue_USD=("Revenue", "median"),
            Avg_Operating_Profit_USD=("Operating_Profit", "mean"),
            Avg_Net_Income_USD=("Net_Income", "mean"),
            Avg_Operating_Margin_Pct=("Operating_Margin_Pct", "mean"),
            Avg_Net_Margin_Pct=("Net_Profit_Margin_Pct", "mean"),
            Avg_EPS=("EPS", "mean"),
            Net_Loss_Ratio=("Net_Loss_Flag", "mean")
        )
        .round(2)
        .reset_index()
    )
    # Format Net_Loss_Ratio as percentage
    sector_benchmark["Net_Loss_Ratio"] = (sector_benchmark["Net_Loss_Ratio"] * 100).round(1).astype(str) + "%"

    print("\n--- SECTOR FINANCIAL PERFORMANCE COMPARISON ---")
    print(sector_benchmark.to_string(index=False))

    # 15. EXPORT FILES
    print(f"\n[Step 15] Exporting outputs...")
    output_dir = os.path.dirname(output_csv_path)

    # 1. Cleaned Dataset
    df_cleaned.to_csv(output_csv_path, index=False)
    print(f" -> Cleaned Dataset: {output_csv_path}")

    # 2. Sector Benchmark Summary
    sector_summary_path = os.path.join(output_dir, "sector_financial_performance.csv")
    sector_benchmark.to_csv(sector_summary_path, index=False)
    print(f" -> Sector Benchmark Summary: {sector_summary_path}")

    # 3. Data Quality Audit Summary
    audit_summary_path = os.path.join(output_dir, "data_cleaning_audit_summary.csv")
    df_quality_summary.to_csv(audit_summary_path, index=False)
    print(f" -> Quality Audit Summary: {audit_summary_path}")

    return df_cleaned, sector_benchmark, df_quality_summary


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "messy_financial_data.csv")
    output_file = os.path.join(current_dir, "cleaned_financial_data.csv")

    clean_financial_dataset(input_file, output_file)
