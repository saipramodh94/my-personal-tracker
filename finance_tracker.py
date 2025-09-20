import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
import sys

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(page_title="Finance Tracker", layout="wide")

# -------------------------------
# Authentication
# -------------------------------
def check_password():
    """Returns `True` if the user had a correct password."""

    def login_attempt():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets["credentials"]["usernames"] and st.secrets["credentials"]["usernames"][st.session_state["username"]] == st.session_state["password"]:
            st.session_state["authenticated"] = True
            st.session_state["user"] = st.session_state["username"] # Store username
            del st.session_state["password"]  # don't store password
            del st.session_state["username"]
        else:
            st.session_state["authenticated"] = False

    if not st.session_state.get("authenticated", False):
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=login_attempt)
        if "authenticated" in st.session_state and not st.session_state.authenticated:
             st.error("Invalid username or password")
        return False
    else:
        return True

if not check_password():
    st.stop() # Do not render the main app if not authenticated

# --- Main App Starts Here ---

# -------------------------------
# Supabase Setup
# -------------------------------
try:
    supabase_url = st.secrets["supabase"]["url"]
    supabase_key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(supabase_url, supabase_key)
except (KeyError, FileNotFoundError):
    st.error("Supabase credentials not found.")
    st.info("Please add your Supabase URL and Key to the Streamlit secrets manager or a local secrets.toml file.")
    sys.exit()

# -------------------------------
# Header with Title and Logout
# -------------------------------
col1, col2 = st.columns([3, 1])
with col1:
    st.title("💰 Personal Finance Tracker")
with col2:
    st.container() # This helps with alignment
    st.write(f"Welcome, {st.session_state.user}!")
    if st.button("Log out"):
        st.session_state.authenticated = False
        if "user" in st.session_state:
            del st.session_state["user"]
        st.rerun()


# -------------------------------
# Category & Subcategory Mapping
# -------------------------------
CATEGORY_MAP = {
    "Income": {
        "Salary": ["-"], "Returns": ["-"], "Others": ["-"],
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
# Supabase Load & Add Functions
# -------------------------------
def get_transactions(person: str) -> pd.DataFrame:
    """Fetches all transactions for a specific person from the Supabase table."""
    try:
        response = supabase.table("transactions").select("*").eq("person", person).order("date", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching data from Supabase: {e}")
        return pd.DataFrame()

def add_transaction(date, person, ttype, category, subcategory, desc, amount):
    """Adds a new transaction row to the Supabase table."""
    try:
        new_row = {
            "date": date.isoformat(), "person": person, "type": ttype,
            "category": category, "sub_category": subcategory,
            "description": desc, "amount": round(amount, 2),
        }
        supabase.table("transactions").insert(new_row).execute()
        st.success("✅ Transaction added successfully!")
    except Exception as e:
        st.error(f"Error adding transaction: {e}")

# -------------------------------
# Formatting Functions
# -------------------------------
def format_amount(amount):
    return f"₹{amount:,.1f}"

def parse_amount(value):
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0

# -------------------------------
# UI Functions
# -------------------------------
def show_summary_table(person):
    df = get_transactions(person)
    if df.empty:
        st.info(f"No transactions yet for {person}.")
        return

    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    df["sub_category"] = df.apply(
        lambda row: row["description"] if row["category"] == "Others" else row["sub_category"],
        axis=1,
    )
    st.subheader(f"📊 {person} - Category Summary")

    total_income = df[df["type"] == "Income"]["amount"].sum()
    total_expense = df[df["type"] == "Expense"]["amount"].sum()
    balance = total_income - total_expense

    summary_df = df[df["type"] == "Expense"].copy()
    if not summary_df.empty:
        summary_df = summary_df.groupby(["category", "sub_category"])["amount"].sum().reset_index()
        summary_df = summary_df.sort_values("category")
        summary_df["Amount"] = summary_df["amount"].apply(format_amount)
        st.dataframe(summary_df[["category", "sub_category", "Amount"]], use_container_width=True, hide_index=True)
    else:
        st.write("No expenses recorded for this person.")

    st.markdown(f"**Total Income:** {format_amount(total_income)}  |  **Total Expense:** {format_amount(total_expense)}  |  **Balance:** {format_amount(balance)}")

# -------------------------------
# Main Streamlit UI
# -------------------------------
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
    subcategories = CATEGORY_MAP[ttype].get(category, ["-"])
    subcategory = st.selectbox("Sub-Category", subcategories, key="subcategory")
    amount_input = st.text_input("Amount", "0", key="amount_input")
    amount = parse_amount(amount_input)
    st.markdown(f"**Entered Amount:** {format_amount(amount)}")

if st.button("Add Transaction"):
    add_transaction(date, person, ttype, category, subcategory, desc, amount)
    st.rerun()

st.divider()
st.header("📊 Expense Summaries")
for p in ["Pramodh", "Manasa", "Ours"]:
    show_summary_table(p)
    st.divider()

