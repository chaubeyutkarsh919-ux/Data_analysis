import os
import random
import numpy as np
import pandas as pd

def generate_messy_financial_dataset(n_rows: int = 1000, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    # Base sector profiles: typical revenue range (in USD), operating margin mean, std
    sectors_config = {
        "Technology": {
            "companies": [
                "CloudScale Technologies", "Apex Quantum Corp", "CyberNova Systems",
                "DataSphere Solutions", "Synapse AI Inc", "MicroLogic Systems",
                "Nexus Software Corp", "OmniSoft Group", "ByteWave Interactive", "InfoCore Global"
            ],
            "rev_range": (150_000_000, 85_000_000_000),
            "op_margin_mean": 0.22,
            "op_margin_std": 0.12,
            "pe_ratio": 32,
        },
        "Financial Services": {
            "companies": [
                "Beacon Capital Group", "Horizon Bancorp", "Vanguardian Trust Co",
                "Sterling Wealth Partners", "Pinnacle Financial Holdings", "Crestview Holdings",
                "Global Reserve Bank", "BlueStone Credit Corp", "Meridian Asset Group", "Apex Financial"
            ],
            "rev_range": (300_000_000, 120_000_000_000),
            "op_margin_mean": 0.28,
            "op_margin_std": 0.10,
            "pe_ratio": 14,
        },
        "Healthcare": {
            "companies": [
                "BioGenix Laboratories", "Vitas Health Systems", "Curative Pharmaceuticals",
                "NovaTherapeutics Inc", "OmniCare Medical Group", "AlphaBio Sciences",
                "SteriMed Diagnostics", "GenePure Therapeutics", "Pulse Health Group", "Aegis BioLabs"
            ],
            "rev_range": (80_000_000, 65_000_000_000),
            "op_margin_mean": 0.15,
            "op_margin_std": 0.16,
            "pe_ratio": 24,
        },
        "Consumer Cyclical": {
            "companies": [
                "Urban Outfitters Group", "Velox Retail Brands", "NextGen Apparel Inc",
                "PrimeConsumer Corp", "Luxe Motors International", "Metro Living Retail",
                "Summit Leisure Brands", "Aura Lifestyle Goods", "Velocity Motors", "TrendSet Brands"
            ],
            "rev_range": (100_000_000, 55_000_000_000),
            "op_margin_mean": 0.08,
            "op_margin_std": 0.06,
            "pe_ratio": 18,
        },
        "Energy": {
            "companies": [
                "PetroDyn Energy Corp", "Solaris Energy Group", "Titan Oil & Gas Ltd",
                "TerraGreen Power Co", "Vortex Resources Inc", "Apex Hydrocarbons",
                "Helios Clean Power", "Crestline Exploration", "Echo Energy Systems", "Nordic Gas Corp"
            ],
            "rev_range": (500_000_000, 95_000_000_000),
            "op_margin_mean": 0.14,
            "op_margin_std": 0.18,
            "pe_ratio": 11,
        },
        "Industrials": {
            "companies": [
                "Aeroflux Dynamics", "Foundry Global Heavy Industries", "Vanguard Logistics",
                "Atlas Heavy Machinery", "Precision Systems Corp", "Continental Freight Corp",
                "SteelCore Industries", "Orbital Aerospace Mfg", "Titan Machine Works", "Pioneer Equipment"
            ],
            "rev_range": (120_000_000, 48_000_000_000),
            "op_margin_mean": 0.11,
            "op_margin_std": 0.07,
            "pe_ratio": 19,
        }
    }

    # Messy Sector variants
    sector_variants = {
        "Technology": ["Technology", "technology", "TECHNOLOGY", " Tech ", "Tech", "Information Technology", "IT"],
        "Financial Services": ["Financial Services", "Financials", "FINANCE", "Fin Services", " Financial Services ", "Banking & Finance"],
        "Healthcare": ["Healthcare", "Health Care", "health care", "HEALTHCARE", "HealthCare ", "Bio/Pharma"],
        "Consumer Cyclical": ["Consumer Cyclical", "consumer cyclical", "Consumer Discretionary", "Cons. Cyclical", "Retail & Consumer"],
        "Energy": ["Energy", "energy", "ENERGY", "Energy & Power", " Oil & Gas ", "Enrgy"],
        "Industrials": ["Industrials", "industrials", "INDUSTRIALS", "Industrial", "Manufacturing ", "Ind."]
    }

    # Messy Company Name corruption functions
    def mess_up_company_name(name: str) -> str:
        r = random.random()
        if r < 0.10:
            return name.upper()
        elif r < 0.20:
            return name.lower()
        elif r < 0.30:
            return f"  {name}  "
        elif r < 0.38:
            # Drop legal suffix
            for suffix in [" Inc", " Corp", " Corporation", " Ltd", " Group", " Co", " Holdings"]:
                if suffix in name:
                    return name.replace(suffix, "")
        elif r < 0.45:
            # Inconsistent suffix spelling
            return name.replace("Corp", "Corporation").replace("Inc", "Inc.")
        return name

    # Messy Value formatters
    def format_messy_currency(val: float, allow_accounting_negative: bool = True) -> any:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return random.choice([np.nan, "N/A", "NA", "-", "None", "null", ""])
        
        r = random.random()
        # 8% missing/corrupted sentinel
        if r < 0.08:
            return random.choice([np.nan, "N/A", "NA", "-", "None", "null", "", "#VALUE!", "TBD"])
        
        is_neg = val < 0
        abs_val = abs(val)

        # 18% abbreviated with suffix (e.g., $12.4M, 1.2B, 450K)
        if r < 0.26:
            if abs_val >= 1_000_000_000:
                s = f"{abs_val / 1_000_000_000:.2f}B"
            elif abs_val >= 1_000_000:
                s = f"{abs_val / 1_000_000:.2f}M"
            else:
                s = f"{abs_val / 1_000:.1f}K"
            
            prefix = random.choice(["$", "$ ", "USD ", "", "US$ "])
            if is_neg:
                return f"({prefix}{s})" if allow_accounting_negative and random.random() < 0.6 else f"-{prefix}{s}"
            return f"{prefix}{s}"
        
        # 25% formatted with commas and currency sign
        if r < 0.51:
            comma_str = f"{abs_val:,.2f}"
            prefix = random.choice(["$", "$ ", "USD ", ""])
            if is_neg:
                if allow_accounting_negative and random.random() < 0.7:
                    return f"({prefix}{comma_str})"
                return f"-{prefix}{comma_str}"
            return f"{prefix}{comma_str}"
        
        # 15% accounting negative in parentheses without currency
        if r < 0.66:
            comma_str = f"{abs_val:,.2f}" if random.random() < 0.5 else f"{abs_val:.2f}"
            if is_neg:
                return f"({comma_str})"
            return comma_str

        # 20% plain string with extra spaces or standard float string
        if r < 0.86:
            sign = "-" if is_neg else ""
            if random.random() < 0.4:
                return f" {sign}{abs_val:.2f} "
            return f"{sign}{abs_val:.2f}"
        
        # Remainder: raw float or integer
        return round(val, 2)

    def format_messy_eps(eps_val: float) -> any:
        if eps_val is None or (isinstance(eps_val, float) and np.isnan(eps_val)):
            return random.choice([np.nan, "N/A", "None", "-"])
        
        r = random.random()
        # Missing values
        if r < 0.07:
            return random.choice([np.nan, "N/A", "NA", "-", "None", "error", "#DIV/0!"])
        
        # Outliers / Fat-finger errors (0.5%)
        if r < 0.08:
            return random.choice([9999.00, -999.00, 145.80, 0.0])

        is_neg = eps_val < 0
        abs_val = abs(eps_val)

        # Dollar formats
        if r < 0.35:
            prefix = random.choice(["$", "$ ", "USD "])
            if is_neg:
                return f"({prefix}{abs_val:.2f})" if random.random() < 0.6 else f"-{prefix}{abs_val:.2f}"
            return f"{prefix}{abs_val:.2f}"
        
        # Accounting parentheses
        if r < 0.55:
            if is_neg:
                return f"({abs_val:.2f})"
            return f"{abs_val:.2f}"
        
        # String with inconsistent decimals
        if r < 0.75:
            decimals = random.choice([1, 3, 4])
            sign = "-" if is_neg else ""
            return f"{sign}{abs_val:.{decimals}f}"
        
        # Raw float
        return round(eps_val, 2)

    def format_messy_margin(margin_val: float) -> any:
        if margin_val is None or (isinstance(margin_val, float) and np.isnan(margin_val)):
            return random.choice([np.nan, "N/A", "None", "-"])
        
        r = random.random()
        # Missing / formula errors
        if r < 0.08:
            return random.choice([np.nan, "N/A", "None", "-", "#DIV/0!", "#VALUE!", "null"])
        
        # Outlier / erroneous percentage
        if r < 0.10:
            return random.choice(["150.0%", "-120.5%", "999%", "0.0%"])

        pct_val = margin_val * 100.0
        is_neg = pct_val < 0
        abs_pct = abs(pct_val)

        # Percentage format with % sign
        if r < 0.50:
            if is_neg:
                return f"({abs_pct:.1f}%)" if random.random() < 0.5 else f"-{abs_pct:.2f}%"
            return f"{abs_pct:.2f}%" if random.random() < 0.7 else f"{abs_pct:.1f}%"

        # Decimal format (0.154 or -0.045)
        if r < 0.75:
            sign = "-" if is_neg else ""
            return f"{sign}{abs(margin_val):.4f}" if random.random() < 0.5 else round(margin_val, 4)

        # Whole number percentage without % symbol (e.g. '15.4' instead of '0.154')
        sign = "-" if is_neg else ""
        return f"{sign}{abs_pct:.2f}"

    def format_messy_date(year: int) -> str:
        r = random.random()
        month = random.choice([3, 6, 9, 12])
        day = 31 if month in [3, 12] else 30
        
        if r < 0.25:
            return f"{year}-{month:02d}-{day:02d}"  # ISO YYYY-MM-DD
        elif r < 0.45:
            return f"{month:02d}/{day:02d}/{year}"  # US MM/DD/YYYY
        elif r < 0.60:
            return f"{day:02d}-{month:02d}-{year}"  # European DD-MM-YYYY
        elif r < 0.75:
            return f"{year}/{month:02d}/{day:02d}"  # YYYY/MM/DD
        elif r < 0.88:
            return f"FY{year}"                      # Fiscal year string
        elif r < 0.95:
            quarter = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}[month]
            return f"{quarter} {year}"
        else:
            return str(year)                        # Just the year

    # Generate records
    records = []
    num_clean_records = n_rows - 40  # Reserve 40 slots for duplicates to reach ~1000

    sectors_list = list(sectors_config.keys())
    years = [2021, 2022, 2023, 2024]

    for i in range(num_clean_records):
        sector = random.choice(sectors_list)
        cfg = sectors_config[sector]
        company = random.choice(cfg["companies"])
        year = random.choice(years)

        # Company Ticker
        ticker_base = "".join([w[0] for w in company.split()[:4]]).upper()
        if random.random() < 0.08:
            ticker = f" {ticker_base} "  # whitespace
        elif random.random() < 0.05:
            ticker = ticker_base.lower()
        elif random.random() < 0.03:
            ticker = np.nan
        else:
            ticker = ticker_base

        # Clean underlying numbers
        min_rev, max_rev = cfg["rev_range"]
        raw_revenue = np.random.uniform(min_rev, max_rev)

        # Operating margin with sector-based distribution
        raw_op_margin = np.random.normal(cfg["op_margin_mean"], cfg["op_margin_std"])
        raw_op_profit = raw_revenue * raw_op_margin

        # Net margin typically lower than operating margin (tax + interest deduction)
        # Occasional accounting anomalies
        tax_and_interest = np.random.uniform(0.02, 0.07)
        raw_net_margin = raw_op_margin - tax_and_interest

        # 3% chance of anomaly: Net Income > Revenue (accounting glitch / restatement error)
        if random.random() < 0.03:
            raw_net_income = raw_revenue * 1.15
            raw_net_margin = 1.15
        else:
            raw_net_income = raw_revenue * raw_net_margin

        # EPS calculation: shares outstanding roughly proportional to company scale
        shares_outstanding = raw_revenue / np.random.uniform(15, 60)
        raw_eps = raw_net_income / shares_outstanding

        # Now apply sector messiness
        if random.random() < 0.05:
            assigned_sector = random.choice(["Unknown", "N/A", "", np.nan, "Other"])
        else:
            assigned_sector = random.choice(sector_variants[sector])

        # Apply company name messiness
        assigned_company = mess_up_company_name(company)
        if random.random() < 0.02:
            assigned_company = np.nan

        # Apply financial messiness
        formatted_revenue = format_messy_currency(raw_revenue)
        formatted_op_profit = format_messy_currency(raw_op_profit)
        formatted_net_income = format_messy_currency(raw_net_income)
        formatted_eps = format_messy_eps(raw_eps)
        formatted_op_margin = format_messy_margin(raw_op_margin)
        formatted_net_margin = format_messy_margin(raw_net_margin)
        formatted_date = format_messy_date(year)

        # Country / Currency column with messy values
        curr_r = random.random()
        if curr_r < 0.70:
            currency = "USD"
        elif curr_r < 0.82:
            currency = "usd"
        elif curr_r < 0.90:
            currency = "$"
        elif curr_r < 0.95:
            currency = "EUR"
        else:
            currency = random.choice([np.nan, "None", "-", "CAD"])

        records.append({
            "Company_ID": f"CMP-{1000 + i}" if random.random() > 0.03 else f"CMP{1000 + i}",
            "Ticker": ticker,
            "Company_Name": assigned_company,
            "Sector": assigned_sector,
            "Reporting_Period": formatted_date,
            "Revenue": formatted_revenue,
            "Operating_Profit": formatted_op_profit,
            "Net_Income": formatted_net_income,
            "EPS": formatted_eps,
            "Operating_Margin": formatted_op_margin,
            "Net_Profit_Margin": formatted_net_margin,
            "Currency": currency
        })

    # Add duplicate rows (to simulate realistic scraping / concatenation duplicates)
    duplicate_samples = random.choices(records, k=40)
    records.extend(duplicate_samples)

    # Shuffle to disperse duplicates throughout the dataset
    random.shuffle(records)

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, "messy_financial_data.csv")

    print(f"Generating 1,000-row messy financial dataset...")
    df = generate_messy_financial_dataset(n_rows=1000, seed=42)

    df.to_csv(output_path, index=False)
    print(f"Dataset successfully created and saved to: {output_path}")
    print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n")

    print("--- FIRST 10 ROWS SAMPLE ---")
    print(df.head(10).to_string())

    print("\n--- DATA TYPES & NON-NULL SUMMARY ---")
    print(df.info())

    print("\n--- SAMPLE VALUES PER COLUMN SHOWCASING MESSINESS ---")
    for col in ["Sector", "Reporting_Period", "Revenue", "Operating_Profit", "Net_Income", "EPS", "Operating_Margin"]:
        samples = [str(x) for x in df[col].dropna().unique()[:8]]
        print(f"{col:<20}: {samples}")
