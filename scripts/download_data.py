import pandas as pd
from ucimlrepo import fetch_ucirepo
from pathlib import Path

# Project directories
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Downloading UCI Online Retail dataset...")

# Fetch dataset
online_retail = fetch_ucirepo(id=352)

# Extract dataset components
features = online_retail.data.features
ids = online_retail.data.ids
targets = online_retail.data.targets

# Include identifier columns where available
dataframes = []

if ids is not None:
    dataframes.append(ids)

if features is not None:
    dataframes.append(features)

if targets is not None:
    dataframes.append(targets)

# Combine all available columns
df = pd.concat(dataframes, axis=1)

# Save original dataset
output_file = RAW_DATA_DIR / "online_retail.csv"
df.to_csv(output_file, index=False)

print("\nDownload completed!")
print(f"Saved to: {output_file}")

print(f"\nRows: {df.shape[0]:,}")
print(f"Columns: {df.shape[1]}")

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst five records:")
print(df.head())

print("\nDataset information:")
print(df.info())
