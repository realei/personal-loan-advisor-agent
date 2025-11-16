# Dataset Setup Guide

## Option 1: Using Kaggle API (Recommended)

### Step 1: Install Kaggle CLI
```bash
pip install kaggle
# or with uv
uv pip install kaggle
```

### Step 2: Get Kaggle API Credentials
1. Go to https://www.kaggle.com/settings
2. Scroll down to "API" section
3. Click "Create New Token"
4. Download `kaggle.json`

### Step 3: Configure Credentials
```bash
# Linux/Mac
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Windows
mkdir %USERPROFILE%\.kaggle
move %USERPROFILE%\Downloads\kaggle.json %USERPROFILE%\.kaggle\
```

### Step 4: Download Dataset
```bash
python scripts/download_data.py
```

## Option 2: Manual Download

### Step 1: Download from Website
1. Visit: https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset
2. Click "Download" button
3. Extract the ZIP file

### Step 2: Place Files
Move the CSV file(s) to:
```
personal-loan-advisor-agent/
└── data/
    └── raw/
        └── loan_approval_dataset.csv
```

## Dataset Description

**Source**: Kaggle - Loan Approval Prediction Dataset
**Creator**: Archit Sharma
**Size**: ~45,000 rows

### Features
- `person_age`: Age of the applicant
- `person_income`: Annual income
- `person_emp_length`: Employment length in years
- `loan_amnt`: Loan amount requested
- `loan_intent`: Purpose of the loan
- `loan_int_rate`: Interest rate
- `loan_percent_income`: Loan amount as percentage of income
- `cb_person_cred_hist_length`: Credit history length
- `credit_score`: Credit score (300-850)
- `previous_loan_defaults_on_file`: Previous defaults (Yes/No)
- `loan_status`: Target variable (Approved/Rejected)

### Usage in This Project
- **Training XGBoost Model**: Credit scoring and approval prediction
- **Evaluation**: Creating realistic test cases
- **Benchmarking**: Comparing agent performance against ML model
