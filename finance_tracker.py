import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
import sys

# -------------------------------
# Supabase Setup
# -------------------------------
# This block attempts to connect to Supabase using credentials stored in Streamlit's secrets manager.
try:
    supabase_url = st.secrets["supabase"]["url"]
    supabase_key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(supabase_url, supabase_key)
except (KeyError, FileNotFoundError):
    st.error("Supabase credentials not found.")
    st.info("Please add your Supabase URL and Key to the Streamlit secrets manager or a local secrets.toml file.")
    sys.exit()


# -------------------------------
# Category & Subcategory Mapping
# -------------------------------
CATEGORY_MAP = {
    "Income": {
        "Salary": ["-"],
        "Returns": ["-"],
        "Others": ["-"],
    },
    "Expense": {
        "Deductions": ["Home Loan", "Interiors Loan", "Home Insurance", "Others"],
        "Entertainment": ["Movies", "Music", "Others"],
        "Investments": ["Stock", "Mutual Funds", "NPS", "Gold", "Others"],
        "Savings": ["Emergency Fund", "Short-Vacation", "Long-Vacation", "Dates"],
        "Insurance": ["Health", "Bike", "Car", "Home", "Others"],
        "Groceries": ["Instamart", "Offline", "Others"],
        "Shopping": ["Clothes", "Electronics", "Others"],
        "Bills": ["Rent", "Mobile", "Internet", "Electricity", "Gas", "Home Maintenance", "Credit Card", "Others"],
        "Travel": ["Petrol", "Cab", "Others"],
        "Vacation": ["Travel", "Food", "Accomomdation", "Others"],
        "Medical": ["Pharmacy", "Tests", "Others"],
        "Food": ["Restaurant", "Home Delivery", "Office", "Others"],
        "Others": ["-"],
    },
}

# -------------------------------
# Supabase Load & Add Functions (Replaces load_data and save_data)
# -------------------------------
def get_transactions(person: str) -> pd.DataFrame:
    """Fetches all transactions for a specific person from the Supabase table."""
    try:
        response = supabase.table("transactions").select("*").eq("person", person).order("date", desc=True).execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Error fetching data from Supabase: {e}")
        return pd.DataFrame()

def add_transaction(date, person, ttype, category, subcategory, desc, amount):
    """Adds a new transaction row to the Supabase table."""
    try:
        new_row = {
            "date": date.isoformat(),
            "person": person,
            "type": ttype,
            "category": category,
            "sub_category": subcategory,
            "description": desc,
            "amount": round(amount, 2),
        }
        supabase.table("transactions").insert(new_row).execute()
        st.success("✅ Transaction added successfully!")
    except Exception as e:
        st.error(f"Error adding transaction: {e}")

# -------------------------------
# Format Amount (simple commas + 1 decimal)
# -------------------------------
def format_amount(amount):
    return f"₹{amount:,.1f}"

def parse_amount(value):
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0

# -------------------------------
# Show Summary Table per person
# -------------------------------
def show_summary_table(person):
    df = get_transactions(person)
    if df.empty:
        st.info(f"No transactions yet for {person}.")
        return

    # Ensure 'amount' column is numeric for calculations
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

    # Use Description as Sub-Category for "Others"
    df["sub_category"] = df.apply(
        lambda row: row["description"] if row["category"] == "Others" else row["sub_category"],
        axis=1,
    )

    st.subheader(f"📊 {person} - Category Summary")

    # Total Income and Expense
    total_income = df[df["type"] == "Income"]["amount"].sum()
    total_expense = df[df["type"] == "Expense"]["amount"].sum()
    balance = total_income - total_expense

    # Expense summary table
    summary_df = df[df["type"] == "Expense"].copy()
    if not summary_df.empty:
        summary_df = summary_df.groupby(["category", "sub_category"])["amount"].sum().reset_index()
        summary_df = summary_df.sort_values("category")  # ascending by category
        summary_df["Amount"] = summary_df["amount"].apply(format_amount)
        st.dataframe(summary_df[["category", "sub_category", "Amount"]], use_container_width=True, hide_index=True)
    else:
        st.write("No expenses recorded for this person.")


    # Totals at bottom
    st.markdown(
        f"**Total Income:** {format_amount(total_income)}  |  "
        f"**Total Expense:** {format_amount(total_expense)}  |  "
        f"**Balance:** {format_amount(balance)}"
    )

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Finance Tracker", layout="wide")
st.title("💰 Personal Finance Tracker")

# Transaction Form
st.header("➕ Add Transaction")
col1, col2 = st.columns(2)

with col1:
    date = st.date_input("Date", datetime.date.today(), key="date")
    person = st.selectbox("Person", ["Pramodh", "Manasa", "Ours"], key="person")
    desc = st.text_input("Description", key="desc")

with col2:
    ttype = st.selectbox("Type", ["Expense", "Income"], key="type")
    categories = list(CATEGORY_MAP[ttype].keys())
    category = st.selectbox("Category", categories, key="category")
    # Dynamically update subcategories based on category selection
    subcategories = CATEGORY_MAP[ttype].get(category, ["-"])
    subcategory = st.selectbox("Sub-Category", subcategories, key="subcategory")
    
    # Amount input as text box
    amount_input = st.text_input("Amount", "0", key="amount_input")
    amount = parse_amount(amount_input)
    st.markdown(f"**Entered Amount:** {format_amount(amount)}")

if st.button("Add Transaction"):
    add_transaction(date, person, ttype, category, subcategory, desc, amount)
    # Rerun to clear the form fields after submission
    st.rerun()

# -------------------------------
# Show Summary Tables for all persons
# -------------------------------
st.divider()
st.header("📊 Expense Summaries")
for p in ["Pramodh", "Manasa", "Ours"]:
    show_summary_table(p)
    st.divider()

