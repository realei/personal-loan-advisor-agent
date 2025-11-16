"""Download Kaggle loan approval dataset.

Requirements:
1. Install kaggle: pip install kaggle
2. Get Kaggle API credentials from https://www.kaggle.com/settings
3. Place kaggle.json in ~/.kaggle/kaggle.json (Linux/Mac) or %USERPROFILE%\.kaggle\kaggle.json (Windows)
"""

import os
import subprocess
import sys
from pathlib import Path


def download_dataset():
    """Download loan approval prediction dataset from Kaggle."""
    # Dataset URL: https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset
    dataset_name = "architsharma01/loan-approval-prediction-dataset"

    # Create data directory
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Check if kaggle is installed
    try:
        subprocess.run(["kaggle", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Kaggle CLI is not installed.")
        print("📦 Please install it: pip install kaggle")
        print("🔑 Then configure API credentials: https://www.kaggle.com/settings")
        sys.exit(1)

    # Check if API credentials exist
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json.exists():
        print("❌ Kaggle API credentials not found.")
        print("🔑 Please download kaggle.json from https://www.kaggle.com/settings")
        print(f"📂 Place it at: {kaggle_json}")
        sys.exit(1)

    # Download dataset
    print(f"⬇️  Downloading dataset: {dataset_name}")
    try:
        subprocess.run(
            ["kaggle", "datasets", "download", "-d", dataset_name, "-p", str(data_dir), "--unzip"],
            check=True
        )
        print(f"✅ Dataset downloaded successfully to: {data_dir}")

        # List downloaded files
        files = list(data_dir.glob("*.csv"))
        if files:
            print("\n📄 Downloaded files:")
            for file in files:
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   - {file.name} ({size_mb:.2f} MB)")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_dataset()
