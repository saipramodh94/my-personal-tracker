import streamlit as st
import pandas as pd
import datetime
from babel.numbers import format_currency
from supabase import create_client, Client
import sys
import uuid

# -------------------------------
# Supabase Setup
# -------------------------------
# This block attempts to connect to Supabase using credentials stored in Streamlit's secrets manager.
# It's designed to work seamlessly both in local development (with a .streamlit/secrets.toml file)
# and when deployed on Streamlit Community Cloud.
try:
    supabase_url = st.secrets["supabase"]["url"]
    supabase_key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(supabase_url, supabase_key)
except (KeyError, FileNotFoundError):
    st.error("Supabase credentials not found.")
    st.info("Please create a `.streamlit/secrets.toml` file with your Supabase URL and Key for local development, or add them to the secrets manager for deployment.")
    sys.exit()

# -------------------------------
# Category & Subcategory Mapping
# -------------------------------
# A dictionary to manage the hierarchy of transaction categories and sub-categories.
CATEGORY_MAP = {
    "Income": {"Salary": ["-"], "Returns": ["-"], "Others": ["-"]},
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
# Database Functions
# -------------------------------
def upload_receipt(file, person: str) -> str:
    """Uploads a receipt file to Supabase Storage and returns the public URL."""
    if not file:
        return None

    # Generate a unique file path to prevent overwrites, organizing by person.
    file_extension = file.name.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"{person}/{unique_filename}"
    
    file_bytes = file.getvalue()

    try:
        # Upload the file to the 'receipts' bucket.
        supabase.storage.from_("receipts").upload(file=file_bytes, path=file_path)
        # Retrieve the public URL for the uploaded file.
        res = supabase.storage.from_("receipts").get_public_url(file_path)
        return res
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        return None

def get_transactions(person: str) -> pd.DataFrame:
    """Fetches all transactions for a specific person from the Supabase table."""
    try:
        response = supabase.table("transactions").select("*").eq("person", person).order("date", desc=True).execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Error fetching data from Supabase: {e}")
        return pd.DataFrame()


def add_transaction(date, person, ttype, category, subcategory, desc, amount, receipt_file):
    """Adds a new transaction row to the Supabase table, including a receipt URL."""
    if not (person and ttype and category and subcategory and amount > 0):
        st.warning("Please fill out all required fields and ensure the amount is greater than zero.")
        return

    # First, upload the receipt if one was provided.
    receipt_url = upload_receipt(receipt_file, person)

    try:
        new_row = {
            "date": date.isoformat(),
            "person": person,
            "type": ttype,
            "category": category,
            "sub_category": subcategory,
            "description": desc,
            "amount": round(amount, 2),
            "receipt_url": receipt_url, # Add the URL to the row.
        }
        supabase.table("transactions").insert(new_row).execute()
        st.success("✅ Transaction added successfully!")
    except Exception as e:
        st.error(f"Error adding transaction: {e}")


# -------------------------------
# UI & Summary Functions
# -------------------------------
def show_summary(person: str):
    """Displays transaction summaries and details for a given person."""
    st.subheader(f"📊 Summary for {person}")
    df = get_transactions(person)
    
    if df.empty:
        st.info(f"No transactions yet for {person}.")
        return

    # Data type conversions for accurate calculations and display.
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    df['date'] = pd.to_datetime(df['date'])
    
    # Create a 'Month-Year' column for filtering.
    df['MonthYear'] = df['date'].dt.strftime('%b-%Y')
    months = sorted(df['MonthYear'].unique(), key=lambda m: datetime.datetime.strptime(m, '%b-%Y'), reverse=True)
    
    selected_month = st.selectbox("Select Month", options=months, key=f"month_{person}")
    df_filtered = df[df['MonthYear'] == selected_month].copy()

    if df_filtered.empty:
        st.info(f"No transactions in {selected_month} for {person}.")
        return

    # --- Expense Breakdown Table ---
    st.markdown("##### Expense Breakdown")
    expense_df = df_filtered[df_filtered["type"]=="Expense"].copy()
    if not expense_df.empty:
        expense_df["sub_category"] = expense_df.apply(lambda row: row["description"] if row["category"]=="Others" else row["sub_category"], axis=1)
        exp_summary = expense_df.groupby(["category", "sub_category"])["amount"].sum().reset_index()
        exp_summary["Amount"] = exp_summary["amount"].apply(lambda x: format_currency(x, "INR", locale="en_IN"))
        exp_summary = exp_summary.sort_values("amount", ascending=False)
        st.dataframe(exp_summary[["category", "sub_category", "Amount"]], use_container_width=True)
    else:
        st.write("No expenses recorded for this month.")

    # --- Totals Table ---
    total_income = df_filtered[df_filtered["type"]=="Income"]["amount"].sum()
    total_expense = expense_df["amount"].sum()
    balance = total_income - total_expense

    summary_data = {
        "Metric": ["Total Income", "Total Expense", "Balance"],
        "Amount": [
            format_currency(total_income, "INR", locale="en_IN"),
            format_currency(total_expense, "INR", locale="en_IN"),
            format_currency(balance, "INR", locale="en_IN")
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    st.table(summary_df)

    # --- Full Transaction List ---
    st.markdown("##### All Transactions this Month")
    # Format the receipt URL to be a clickable markdown link for display.
    df_display = df_filtered.copy()
    df_display['receipt'] = df_display['receipt_url'].apply(lambda x: f"[View Receipt]({x})" if pd.notna(x) else "No file")
    df_display['date'] = df_display['date'].dt.strftime('%d-%b-%Y')
    st.dataframe(df_display[['date', 'description', 'category', 'amount', 'receipt']], use_container_width=True)

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Finance Tracker", layout="wide")
st.title("💰 Personal Finance Tracker")

# Use a form for adding transactions to prevent the page from re-running on every widget interaction.
with st.form("transaction_form", clear_on_submit=True):
    st.header("➕ Add a New Transaction")
    col1, col2, col3 = st.columns(3)

    with col1:
        date = st.date_input("Date", datetime.date.today())
        person = st.selectbox("Person", ["Pramodh", "Manasa", "Ours"])
        desc = st.text_input("Description (optional)")

    with col2:
        ttype = st.selectbox("Type", ["Expense", "Income"], key="type")
        categories = list(CATEGORY_MAP[ttype].keys())
        category = st.selectbox("Category", categories, key="category")
        subcategories = CATEGORY_MAP[ttype][category]
        subcategory = st.selectbox("Sub-Category", subcategories, key="subcategory")

    with col3:
        amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")
        receipt_file = st.file_uploader("Upload Receipt (Optional)", type=['png', 'jpg', 'jpeg', 'pdf'])

    # The submit button for the form.
    submitted = st.form_submit_button("Add Transaction")
    if submitted:
        add_transaction(date, person, ttype, category, subcategory, desc, amount, receipt_file)

st.divider()

st.header("📈 Monthly Summaries")
# Use tabs to neatly organize the summaries for each person.
tabs = st.tabs(["Pramodh", "Manasa", "Ours"])
persons = ["Pramodh", "Manasa", "Ours"]

for i, tab in enumerate(tabs):
    with tab:
        show_summary(persons[i])

