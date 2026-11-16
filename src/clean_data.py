import pandas as pd
from pathlib import Path

# Define paths
RAW_DATA = Path("data/raw/wdi_india_data.csv")
META_IND = Path("data/raw/wdi_indicators_meta.csv")
OUT_FILE = Path("data/processed/india_econ_trade.parquet")

# Target indicators for Economic Transformation & Trade
TARGET_INDICATORS = [
    "NY.GDP.MKTP.KD",
    "NY.GDP.PCAP.KD",
    "NY.GNP.PCAP.KD.ZG",
    "NV.AGR.TOTL.ZS",
    "NV.IND.MANF.ZS",
    "NV.SRV.TOTL.ZS",
    "NE.TRD.GNFS.ZS",
    "NE.EXP.GNFS.ZS",
    "NE.IMP.GNFS.ZS",
    "TM.TAX.MRCH.WM.AR.ZS",
    "TX.VAL.TECH.MF.ZS",
    "BX.GSR.CCIS.CD",
    "BX.TRF.PWKR.DT.GD.ZS",
    "BX.KLT.DINV.CD.WD",
]

def main():
    # Skip the first 4 metadata rows in the main WDI CSV
    df = pd.read_csv(RAW_DATA, skiprows=4)
    
    # Filter for our target indicators
    df = df[df["Indicator Code"].isin(TARGET_INDICATORS)].copy()
    
    # Identify year columns (1960 to 2025)
    year_cols = [col for col in df.columns if col.isdigit()]
    
    # Reshape from wide to long format
    df_long = df.melt(
        id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],
        value_vars=year_cols,
        var_name="Year",
        value_name="Value"
    )
    #print(df_long)
    
    # Clean data types
    df_long["Year"] = df_long["Year"].astype(int)
    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
    df_long = df_long.dropna(subset=["Value"]).sort_values(["Indicator Code", "Year"])
    
    # Save as Parquet for fast loading in Notebooks & Streamlit
    df_long.to_parquet(OUT_FILE, index=False)
    print(f"Saved {len(df_long):,} clean records to {OUT_FILE}")

if __name__ == "__main__":
    main()
