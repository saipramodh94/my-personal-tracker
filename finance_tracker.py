import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
import sys
import plotly.express as px

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(page_title="Personal Hub", layout="wide", initial_sidebar_state="expanded")

# -------------------------------
# Custom Styling (Theme-Aware & Final Version)
# -------------------------------
def local_css():
    st.markdown("""
        <style>
            /* --- Universal Styles (Apply to BOTH themes) --- */
            * {
                font-family: 'Inter', sans-serif;
            }
            /* Input field reset to remove blue glow from password 'eye' icon */
            div[data-testid="stTextInput"] button:focus,
            div[data-testid="stTextInput"] button:focus-visible {
                outline: none !important;
                box-shadow: none !important;
                border-color: transparent !important;
                background-color: transparent !important;
            }
            /* General Buttons (Sea Blue) - FOR MAIN CONTENT AREA */
            div[data-testid="stFullScreenFrame"] div[data-testid="stButton"] > button,
            div[data-testid="stForm"] button {
                background-color: #00dfff !important;
                color: #1a1a1a !important;
                font-weight: bold;
                border: none !important;
                border-radius: 20px;
                padding: 10px 24px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
            div[data-testid="stFullScreenFrame"] div[data-testid="stButton"] > button:hover,
            div[data-testid="stForm"] button:hover {
                background-color: #00b8d4 !important;
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                transform: translateY(-2px);
            }
            
            /* --- Sidebar Button Styling (Transparent) --- */
            div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
                background-color: transparent !important;
                border: 1px solid #6c757d !important;
                border-radius: 10px !important;
                padding: 8px 16px !important;
            }
             body[data-theme="dark"] div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
                color: #FAFAFA !important;
            }
             body[data-theme="light"] div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
                color: #31333F !important;
            }
            
            /* --- Logout Button Styling --- */
            .logout-button-container div[data-testid="stButton"] > button {
                background-color: #6c757d !important; /* Grey color */
                color: white !important;
                padding: 4px 12px !important; /* Smaller padding */
                font-size: 14px !important;
                font-weight: normal !important;
                border-radius: 15px !important;
            }
            .logout-button-container div[data-testid="stButton"] > button:hover {
                background-color: #5a6268 !important; /* Darker grey on hover */
            }

            /* Metric Values (Gold) */
            div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
                color: #FFD700 !important;
            }

            /* --- Section Container with Border --- */
            .section-container {
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }

            /* --- Light Theme Specific Styles --- */
            body[data-theme="light"] .stApp { background-color: #f0f2f6; }
            body[data-theme="light"] h1, body[data-theme="light"] h2, body[data-theme="light"] h3 { color: #262730 !important; }
            body[data-theme="light"] p, body[data-theme="light"] li, body[data-theme="light"] label { color: #31333F !important; }
            body[data-theme="light"] .section-container, body[data-theme="light"] div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e0e0e0; }
            body[data-theme="light"] div[data-testid="stMetric"] > label { color: #5f6368; }

            /* --- Dark Theme Specific Styles --- */
            body[data-theme="dark"] .stApp { background-color: #0E1117; }
            body[data-theme="dark"] h1, body[data-theme="dark"] h2, body[data-theme="dark"] h3, body[data-theme="dark"] p, body[data-theme="dark"] li, body[data-theme="dark"] label { color: #FAFAFA !important; }
            body[data-theme="dark"] .section-container, body[data-theme="dark"] div[data-testid="stMetric"] { background-color: #262730; border: 1px solid #303338; }
            body[data-theme="dark"] div[data-testid="stMetric"] > label { color: #aab8c5; }
        </style>
    """, unsafe_allow_html=True)

local_css()

# -------------------------------
# Authentication
# -------------------------------
def check_password():
    if st.session_state.get("authenticated", False):
        return True

    st.title("Welcome Pramodh & Manasa")
    st.write("")

    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if st.session_state.get("username") in st.secrets["credentials"]["usernames"] and \
                   st.secrets["credentials"]["usernames"][st.session_state.get("username")] == st.session_state.get("password"):
                    
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = st.session_state.get("username")
                    if "password" in st.session_state: del st.session_state["password"]
                    if "username" in st.session_state: del st.session_state["username"]
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    return False

if not check_password():
    st.stop()

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
    st.info("Please add Supabase URL and Key to Streamlit secrets.")
    st.stop()

# -------------------------------
# Category Mapping
# -------------------------------
CATEGORY_MAP = {
    "Income": {"Salary": ["-"], "Returns": ["-"], "Others": ["-"]},
    "Expense": {
        "Deductions": ["Home Loan", "Interiors Loan", "Home Insurance", "Others"],
        "Entertainment": ["Movies", "Music", "Others"], "Investments": ["Stock", "Mutual Funds", "NPS", "Gold", "Others"],
        "Savings": ["Emergency Fund", "Short-Vacation", "Long-Vacation", "Dates"],
        "Insurance": ["Health", "Bike", "Car", "Home", "Others"], "Groceries": ["Instamart", "Offline", "Others"],
        "Shopping": ["Clothes", "Electronics", "Others"],
        "Bills": ["Rent", "Mobile", "Internet", "Electricity", "Gas", "Home Maintenance", "Credit Card", "Others"],
        "Travel": ["Petrol", "Cab", "Others"], "Vacation": ["Travel", "Food", "Accomomdation", "Others"],
        "Medical": ["Pharmacy", "Tests", "Others"],"Food": ["Restaurant", "Home Delivery", "Office", "Others"],
        "Others": ["-"],
    },
}

# -------------------------------
# Supabase CRUD Functions
# -------------------------------
@st.cache_data(ttl=600)
def get_all_transactions() -> pd.DataFrame:
    try:
        response = supabase.table("transactions").select("*").order("date", desc=True).execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def add_transaction(date, person, ttype, category, subcategory, desc, amount):
    try:
        new_row = {"date": date.isoformat(), "person": person, "type": ttype, "category": category, "sub_category": subcategory, "description": desc, "amount": round(amount, 2)}
        supabase.table("transactions").insert(new_row).execute()
        st.success("✅ Transaction added!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error adding transaction: {e}")

def update_transaction(transaction_id, date, person, ttype, category, subcategory, desc, amount):
    try:
        updated_row = {"date": date.isoformat(), "person": person, "type": ttype, "category": category, "sub_category": subcategory, "description": desc, "amount": round(amount, 2)}
        supabase.table("transactions").update(updated_row).eq("id", transaction_id).execute()
        st.success("✅ Transaction updated!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error updating transaction: {e}")

def delete_transaction(transaction_id):
    try:
        supabase.table("transactions").delete().eq("id", transaction_id).execute()
        st.success("✅ Transaction deleted!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error deleting transaction: {e}")

# -------------------------------
# Formatting Functions
# -------------------------------
def format_amount(amount):
    return f"₹{amount:,.1f}"

def parse_amount(value):
    try:
        return float(str(value).replace(",", "").replace("₹", ""))
    except (ValueError, TypeError):
        return 0.0

# ===============================
# PAGE DEFINITIONS
# ===============================
def page_home():
    st.header("🏠 Home Dashboard")
    st.write("Your central hub for a quick overview of everything.")
    
    st.subheader("Financial Summary")
    df = get_all_transactions()
    if df.empty:
        st.info("No transactions yet. Add a transaction in the 'Finances' section to see your summary.")
    else:
        total_income = df[df["type"] == "Income"]["amount"].sum()
        total_expense = df[df["type"] == "Expense"]["amount"].sum()
        net_balance = total_income - total_expense
        num_transactions = len(df)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="Total Income", value=format_amount(total_income))
        col2.metric(label="Total Expense", value=format_amount(total_expense), delta=format_amount(-total_expense))
        col3.metric(label="Net Balance", value=format_amount(net_balance))
        col4.metric(label="Total Transactions", value=num_transactions)

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("Upcoming Dates summary will be shown here.")
    with col2:
        st.info("Reminders summary will be shown here.")
    with col3:
        st.info("Travel Plans summary will be shown here.")


def page_add_transaction():
    st.header("➕ Add New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", datetime.date.today())
        person = st.selectbox("Person", ["Pramodh", "Manasa", "Ours"])
        ttype = st.selectbox("Type", ["Expense", "Income"])
    with col2:
        categories = list(CATEGORY_MAP.get(ttype, {}).keys())
        category = st.selectbox("Category", categories)
        subcategories = CATEGORY_MAP.get(ttype, {}).get(category, ["-"])
        subcategory = st.selectbox("Sub-Category", subcategories)
        desc = st.text_input("Description")
        amount_input = st.text_input("Amount", "0")
    
    _, submit_col, _ = st.columns([1, 0.5, 1])
    with submit_col:
        if st.button("Add Transaction"):
            amount = parse_amount(amount_input)
            if amount > 0:
                add_transaction(date, person, ttype, category, subcategory, desc, amount)
                st.rerun()
            else:
                st.warning("Amount must be greater than zero.")

def page_update_transaction():
    st.header("✏️ Update / Delete a Transaction")
    df = get_all_transactions()
    if df.empty:
        st.info("No transactions available to update.")
        return

    st.subheader("Recent Transactions")
    st.dataframe(df[['id', 'date', 'person', 'category', 'description', 'amount']].head(20), use_container_width=True, hide_index=True)
    st.divider()

    transaction_id_to_edit = st.number_input("Enter Transaction ID to Edit/Delete", min_value=1, step=1, value=None)
    if transaction_id_to_edit:
        selected_row_df = df[df['id'] == transaction_id_to_edit]
        if not selected_row_df.empty:
            selected_row = selected_row_df.iloc[0]
            st.subheader("Edit Transaction Details")
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date", value=selected_row['date'], key=f"date_{transaction_id_to_edit}")
                person = st.selectbox("Person", ["Pramodh", "Manasa", "Ours"], index=["Pramodh", "Manasa", "Ours"].index(selected_row['person']), key=f"person_{transaction_id_to_edit}")
                ttype = st.selectbox("Type", ["Expense", "Income"], index=["Expense", "Income"].index(selected_row['type']), key=f"type_{transaction_id_to_edit}")
            with col2:
                categories = list(CATEGORY_MAP.get(ttype, {}).keys())
                cat_index = categories.index(selected_row['category']) if selected_row['category'] in categories else 0
                category = st.selectbox("Category", categories, index=cat_index, key=f"category_{transaction_id_to_edit}")
                subcategories = CATEGORY_MAP.get(ttype, {}).get(category, ["-"])
                sub_cat_index = subcategories.index(selected_row['sub_category']) if selected_row['sub_category'] in subcategories else 0
                subcategory = st.selectbox("Sub-Category", subcategories, index=sub_cat_index, key=f"subcategory_{transaction_id_to_edit}")
                desc = st.text_input("Description", value=selected_row['description'], key=f"desc_{transaction_id_to_edit}")
                amount_input = st.text_input("Amount", value=str(selected_row['amount']), key=f"amount_{transaction_id_to_edit}")
            
            update_col, delete_col = st.columns([1, 1])
            with update_col:
                if st.button("Update Transaction", key=f"update_btn_{transaction_id_to_edit}"):
                    amount = parse_amount(amount_input)
                    if amount > 0:
                        update_transaction(transaction_id_to_edit, date, person, ttype, category, subcategory, desc, amount)
                        st.rerun()
                    else:
                        st.warning("Amount must be greater than zero.")
            with delete_col:
                if st.button("Delete Transaction", key=f"delete_btn_{transaction_id_to_edit}"):
                    delete_transaction(transaction_id_to_edit)
                    st.rerun()
        else:
            st.warning("Transaction ID not found.")

def page_view_summary():
    st.header("📊 Expense Summaries")
    df = get_all_transactions()
    for p in ["Pramodh", "Manasa", "Ours"]:
        st.subheader(f"👤 {p}'s Summary")
        df_person = df[df["person"] == p]
        if df_person.empty:
            st.info(f"No transactions yet for {p}.")
        else:
            df_person['amount'] = pd.to_numeric(df_person['amount'], errors='coerce').fillna(0)
            df_person["sub_category"] = df_person.apply(lambda row: row["description"] if row["category"] == "Others" else row["sub_category"], axis=1)
            total_income = df_person[df_person["type"] == "Income"]["amount"].sum()
            total_expense = df_person[df_person["type"] == "Expense"]["amount"].sum()
            balance = total_income - total_expense
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Income", format_amount(total_income))
            col2.metric("Total Expense", format_amount(total_expense))
            col3.metric("Balance", format_amount(balance))
            summary_df = df_person[df_person["type"] == "Expense"].copy()
            if not summary_df.empty:
                summary_df = summary_df.groupby(["category", "sub_category"])["amount"].sum().reset_index()
                summary_df["Amount"] = summary_df["amount"].apply(format_amount)
                st.dataframe(summary_df.sort_values("amount", ascending=False)[["category", "sub_category", "Amount"]], use_container_width=True, hide_index=True)
            else:
                st.write("No expenses recorded.")
        st.divider()

# ===============================
# MAIN APP UI & NAVIGATION
# ===============================
# --- Header and Logout ---
_, user_col, logout_col = st.columns([0.75, 0.15, 0.1])
with user_col:
    st.markdown(f"<div style='text-align: right; padding-top: 10px;'>Welcome, {st.session_state.get('user', '')}!</div>", unsafe_allow_html=True)
with logout_col:
    st.markdown('<div class="logout-button-container" style="padding-top: 10px;">', unsafe_allow_html=True)
    if st.button("Log out", key="logout_main"):
        st.session_state.authenticated = False
        if "user" in st.session_state: del st.session_state["user"]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Sidebar Navigation ---
st.sidebar.title("App Sections")

if 'page' not in st.session_state:
    st.session_state.page = "Home"

with st.sidebar:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "Home"
        st.rerun()

    if st.button("💰 Finances", use_container_width=True):
        if not st.session_state.page.startswith("Finances"):
            st.session_state.page = "Finances_Add Transaction"
        st.rerun()
    
    if st.session_state.page.startswith("Finances"):
        sub_page_options = ["Add Transaction", "Update / Delete", "View Summaries"]
        
        try:
            current_sub_page_str = st.session_state.page.split("_")[1].replace("_", " ")
            current_index = sub_page_options.index(current_sub_page_str)
        except (ValueError, IndexError):
            current_index = 0 
        
        finance_sub_page = st.radio(
            "Finance Pages",
            sub_page_options,
            key="finance_sub_page",
            label_visibility="collapsed",
            index=current_index
        )
        new_page_state = f"Finances_{finance_sub_page.replace(' ', '_')}"
        if st.session_state.page != new_page_state:
            st.session_state.page = new_page_state
            st.rerun()

    if st.button("✅ To-Do", use_container_width=True):
        st.session_state.page = "To-Do"
        st.rerun()
    if st.button("⏰ Reminders", use_container_width=True):
        st.session_state.page = "Reminders"
        st.rerun()
    if st.button("🗓️ Important Dates", use_container_width=True):
        st.session_state.page = "Important Dates"
        st.rerun()
    if st.button("✈️ Travel", use_container_width=True):
        st.session_state.page = "Travel"
        st.rerun()

# --- Page Routing ---
current_page = st.session_state.get('page', 'Home')

if current_page == "Home":
    page_home()
elif current_page == "Finances_Add_Transaction":
    page_add_transaction()
elif current_page == "Finances_Update_/_Delete":
    page_update_transaction()
elif current_page == "Finances_View_Summaries":
    page_view_summary()
elif current_page == "To-Do":
    st.header("✅ To-Do List")
    st.info("This feature is coming soon!")
elif current_page == "Reminders":
    st.header("⏰ Reminders")
    st.info("This feature is coming soon!")
elif current_page == "Important Dates":
    st.header("🗓️ Important Dates")
    st.info("This feature is coming soon!")
elif current_page == "Travel":
    st.header("✈️ Travel Planner")
    st.info("This feature is coming soon!")
else:
    page_home()

