# Personal Finance Tracker

A portfolio-ready project to analyze income and expenses, visualize spending patterns, and forecast future expenses.
Built with **Python, Pandas, Plotly, Streamlit**.

## Features
- Upload a CSV of transactions (or use the provided sample in `data/transactions.csv`)
- Dashboard with:
  - Summary KPIs (Income, Expenses, Savings)
  - Category-wise distribution
  - Monthly trends
  - Top expenses
- Simple forecasting (baseline) for next month's expenses
- Filters by date range and category
- Download cleaned/filtered data

## Project Structure
```
finance_tracker/
├─ app/
│  └─ dashboard.py
├─ data/
│  └─ transactions.csv
├─ notebooks/
│  └─ analysis.ipynb
├─ reports/
│  └─ insights.md
├─ requirements.txt
└─ README.md
```

## Quickstart

### 1) Create a virtual environment (optional but recommended)
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run the Streamlit app
```bash
streamlit run app/dashboard.py
```

### 4) Open in browser
Streamlit prints a local URL. Open it and explore the dashboard.

## Data Format
CSV columns (provided in `data/transactions.csv`):
- `Date` (YYYY-MM-DD)
- `Description` (text)
- `Category` (e.g., Salary, Food, Rent, Transport, etc.)
- `Amount` (numeric)
- `Type` (Income or Expense)
- `Payment_Method` (UPI/Card/Cash/Bank Transfer)

## Notes
- Replace `data/transactions.csv` with your own bank/app exports if you prefer.
- If your columns differ, use the `Column Mapping` section in the app to align them.
