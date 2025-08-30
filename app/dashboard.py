import io
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Personal Finance Tracker", layout="wide")

@st.cache_data
def load_data(uploaded):
    if uploaded is None:
        df = pd.read_csv("data/transactions.csv")
    else:
        df = pd.read_csv(uploaded)
    # Basic cleaning
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    # Standardize text columns if present
    for col in ["Category","Type","Payment_Method","Description"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": ""})
    # Ensure Amount numeric
    if "Amount" in df.columns:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
    # Derive month/year
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
    return df

def kpi_card(label, value):
    st.metric(label, f"{value:,.0f}")

st.title("💰 Personal Finance Tracker")

with st.sidebar:
    st.header("Data Source")
    uploaded = st.file_uploader("Upload transactions CSV", type=["csv"], help="Leave empty to use the sample data.")
    st.caption("Expected columns: Date, Description, Category, Amount, Type, Payment_Method")
    st.divider()
    st.header("Column Mapping (optional)")
    st.write("If your CSV uses different column names, rename them below and re-upload.")

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
    try:
        df_existing = pd.read_csv("data/transactions.csv")
        df_existing = pd.concat([df_existing, pd.DataFrame([new_entry])], ignore_index=True)
    except FileNotFoundError:
        df_existing = pd.DataFrame([new_entry])

    df_existing.to_csv("data/transactions.csv", index=False)
    st.success("✅ Transaction added successfully! Refresh to see updated dashboard.")

df = load_data(uploaded)

# Filters
st.sidebar.header("Filters")
min_date, max_date = df["Date"].min(), df["Date"].max()
date_range = st.sidebar.date_input("Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)

categories = ["All"] + sorted(df["Category"].dropna().unique().tolist()) if "Category" in df.columns else ["All"]
selected_cat = st.sidebar.selectbox("Category", categories, index=0)

type_list = ["All"] + sorted(df["Type"].dropna().unique().tolist()) if "Type" in df.columns else ["All"]
selected_type = st.sidebar.selectbox("Type", type_list, index=0)

mask = (df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1])
if selected_cat != "All":
    mask &= (df["Category"] == selected_cat)
if selected_type != "All":
    mask &= (df["Type"] == selected_type)

fdf = df.loc[mask].copy()

# KPIs
col1, col2, col3, col4 = st.columns(4)
total_income = fdf.loc[fdf["Type"] == "Income", "Amount"].sum()
total_expense = fdf.loc[fdf["Type"] == "Expense", "Amount"].sum()
savings = total_income - total_expense
avg_daily_spend = fdf.loc[fdf["Type"] == "Expense"].groupby(fdf["Date"].dt.date)["Amount"].sum().mean() if not fdf.empty else 0

with col1: kpi_card("Total Income", total_income)
with col2: kpi_card("Total Expense", total_expense)
with col3: kpi_card("Savings", savings)
with col4: kpi_card("Avg Daily Spend", avg_daily_spend if not np.isnan(avg_daily_spend) else 0)

st.divider()

# Charts
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

# Simple baseline forecast: next-month expense = average of last 3 months
st.subheader("🔮 Simple Expense Forecast (baseline)")
if not fdf.empty:
    monthly_expense = fdf[fdf["Type"]=="Expense"].groupby("YearMonth")["Amount"].sum().reset_index()
    if len(monthly_expense) >= 3:
        forecast = monthly_expense["Amount"].tail(3).mean()
        st.write(f"Estimated next month's expense: **{forecast:,.0f}** (average of last 3 months)")
    else:
        st.write("Not enough months to forecast. Add more data over time.")

st.divider()
st.subheader("📥 Download Filtered Data")
if not fdf.empty:
    buff = io.StringIO()
    fdf.to_csv(buff, index=False)
    st.download_button("Download CSV", data=buff.getvalue(), file_name="filtered_transactions.csv", mime="text/csv")

st.divider()
st.caption("Tip: Replace data/transactions.csv with your own exported bank/app statements for real analysis.")
