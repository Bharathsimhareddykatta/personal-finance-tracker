import io
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Personal Finance Tracker", layout="wide")

# Google Sheets setup
SHEET_NAME = "transactions"  # Change to your sheet name
SCOPE = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

# Use secrets if deployed, else local credentials.json
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
except:
    st.error("⚠️ Google Sheets credentials not found. Upload credentials.json or set in Streamlit Secrets.")
    st.stop()

client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

def load_data(uploaded=None):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=["Date", "Category", "Description", "Amount", "Type", "Payment_Method"])

    # Cleaning
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)

    for col in ["Category", "Type", "Payment_Method", "Description"]:
        df[col] = df[col].astype(str).str.strip().replace({"nan": ""})

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
    return df

def add_transaction(entry):
    sheet.append_row([entry["Date"], entry["Category"], entry["Description"],
                      entry["Amount"], entry["Type"], entry["Payment_Method"]])

def kpi_card(label, value):
    st.metric(label, f"{value:,.0f}")

st.title("💰 Personal Finance Tracker (Google Sheets)")

# --- Sidebar Add Transaction ---
st.sidebar.header("➕ Add New Transaction")
with st.sidebar.form("add_expense_form"):
    new_date = st.date_input("Date", datetime.today())
    new_category = st.text_input("Category (e.g., Food, Transport, Salary)")
    new_description = st.text_input("Description")
    new_amount = st.number_input("Amount", min_value=0.0, step=100.0)
    new_type = st.selectbox("Type", ["Expense", "Income"])
    new_payment = st.selectbox("Payment Method", ["Cash", "UPI", "Card", "Bank Transfer"])
    submitted = st.form_submit_button("Add Transaction")

if submitted:
    new_entry = {
        "Date": new_date.strftime("%Y-%m-%d"),
        "Category": new_category,
        "Description": new_description,
        "Amount": new_amount,
        "Type": new_type,
        "Payment_Method": new_payment
    }
    add_transaction(new_entry)
    st.success("✅ Transaction added successfully! Saved to Google Sheets.")

# --- Load Data ---
df = load_data()

# --- Filters ---
st.sidebar.header("Filters")
if not df.empty:
    min_date, max_date = df["Date"].min(), df["Date"].max()
    date_range = st.sidebar.date_input("Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)
else:
    date_range = (datetime.today(), datetime.today())

categories = ["All"] + sorted(df["Category"].dropna().unique().tolist()) if not df.empty else ["All"]
selected_cat = st.sidebar.selectbox("Category", categories, index=0)

type_list = ["All"] + sorted(df["Type"].dropna().unique().tolist()) if not df.empty else ["All"]
selected_type = st.sidebar.selectbox("Type", type_list, index=0)

mask = (df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1]) if not df.empty else []
if selected_cat != "All":
    mask &= (df["Category"] == selected_cat)
if selected_type != "All":
    mask &= (df["Type"] == selected_type)

fdf = df.loc[mask].copy() if not df.empty else pd.DataFrame()

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
total_income = fdf.loc[fdf["Type"] == "Income", "Amount"].sum() if not fdf.empty else 0
total_expense = fdf.loc[fdf["Type"] == "Expense", "Amount"].sum() if not fdf.empty else 0
savings = total_income - total_expense
avg_daily_spend = fdf.loc[fdf["Type"] == "Expense"].groupby(fdf["Date"].dt.date)["Amount"].sum().mean() if not fdf.empty else 0

with col1: kpi_card("Total Income", total_income)
with col2: kpi_card("Total Expense", total_expense)
with col3: kpi_card("Savings", savings)
with col4: kpi_card("Avg Daily Spend", avg_daily_spend if not np.isnan(avg_daily_spend) else 0)

st.divider()

# --- Charts ---
tab1, tab2, tab3 = st.tabs(["Category Breakdown", "Monthly Trend", "Top Expenses"])

with tab1:
    if not fdf.empty:
        by_cat = fdf.groupby(["Type","Category"], dropna=False)["Amount"].sum().reset_index()
        colA, colB = st.columns(2)
        with colA:
            exp = by_cat[by_cat["Type"]=="Expense"]
            if not exp.empty:
                fig = px.pie(exp, names="Category", values="Amount", title="Expenses by Category")
                st.plotly_chart(fig, use_container_width=True)
        with colB:
            inc = by_cat[by_cat["Type"]=="Income"]
            if not inc.empty:
                fig = px.pie(inc, names="Category", values="Amount", title="Income by Category")
                st.plotly_chart(fig, use_container_width=True)

with tab2:
    if not fdf.empty:
        trend = fdf.groupby(["YearMonth","Type"])["Amount"].sum().reset_index()
        fig = px.bar(trend, x="YearMonth", y="Amount", color="Type", barmode="group", title="Monthly Income vs Expense")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    if not fdf.empty:
        expenses_only = fdf[fdf["Type"]=="Expense"].nlargest(15, "Amount")
        if not expenses_only.empty:
            fig = px.bar(expenses_only.sort_values("Amount"), x="Amount", y="Description", orientation="h", title="Top 15 Expense Items")
            st.plotly_chart(fig, use_container_width=True)

st.divider()

# Forecast
st.subheader("🔮 Simple Expense Forecast (baseline)")
if not fdf.empty:
    monthly_expense = fdf[fdf["Type"]=="Expense"].groupby("YearMonth")["Amount"].sum().reset_index()
    if len(monthly_expense) >= 3:
        forecast = monthly_expense["Amount"].tail(3).mean()
        st.write(f"Estimated next month's expense: **{forecast:,.0f}** (average of last 3 months)")
    else:
        st.write("Not enough months to forecast. Add more data over time.")

# Download filtered data
st.divider()
st.subheader("📥 Download Filtered Data")
if not fdf.empty:
    buff = io.StringIO()
    fdf.to_csv(buff, index=False)
    st.download_button("Download CSV", data=buff.getvalue(), file_name="filtered_transactions.csv", mime="text/csv")
