import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
import sys

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(page_title="Personal Hub", layout="wide", initial_sidebar_state="expanded")

# -------------------------------
# Custom Styling
# -------------------------------
def local_css():
    st.markdown("""
        <style>
            /* --- Universal Styles --- */
            * { font-family: 'Inter', sans-serif; }
            div[data-testid="stTextInput"] button:focus,
            div[data-testid="stTextInput"] button:focus-visible {
                outline: none !important; box-shadow: none !important;
                border-color: transparent !important; background-color: transparent !important;
            }
            div[data-testid="stFullScreenFrame"] div[data-testid="stButton"] > button,
            div[data-testid="stForm"] button {
                background-color: #00dfff !important; color: #1a1a1a !important;
                font-weight: bold; border: none !important; border-radius: 20px;
                padding: 10px 24px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
            div[data-testid="stFullScreenFrame"] div[data-testid="stButton"] > button:hover,
            div[data-testid="stForm"] button:hover {
                background-color: #00b8d4 !important; box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                transform: translateY(-2px);
            }
            div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
                background-color: transparent !important; border: 1px solid #6c757d !important;
                border-radius: 10px !important; padding: 8px 16px !important;
            }
            body[data-theme="dark"] div[data-testid="stSidebar"] div[data-testid="stButton"] > button { color: #FAFAFA !important; }
            body[data-theme="light"] div[data-testid="stSidebar"] div[data-testid="stButton"] > button { color: #31333F !important; }
            .logout-button-container div[data-testid="stButton"] > button {
                background-color: #6c757d !important; color: white !important;
                padding: 4px 12px !important; font-size: 14px !important;
                font-weight: normal !important; border-radius: 15px !important;
            }
            .logout-button-container div[data-testid="stButton"] > button:hover { background-color: #5a6268 !important; }
            div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #FFD700 !important; }
            .section-container {
                border-radius: 10px; padding: 20px; margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
            body[data-theme="light"] .stApp { background-color: #f0f2f6; }
            body[data-theme="light"] h1, body[data-theme="light"] h2, body[data-theme="light"] h3 { color: #262730 !important; }
            body[data-theme="light"] p, body[data-theme="light"] li, body[data-theme="light"] label { color: #31333F !important; }
            body[data-theme="light"] .section-container, body[data-theme="light"] div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e0e0e0; }
            body[data-theme="light"] div[data-testid="stMetric"] > label { color: #5f6368; }
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
            submitted = st.form_submit_button("Login", width='stretch')

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
# Category Mapping (for Finances)
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
# SUPABASE CRUD FUNCTIONS
# ===============================

# --- Generic & Reusable Functions ---
@st.cache_data(ttl=300)
def get_all_data(table_name):
    try:
        response = supabase.table(table_name).select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(response.data)
        # Convert date columns if they exist
        for col in ['date', 'due_date', 'reminder_date', 'event_date', 'start_date', 'end_date']:
             if col in df.columns:
                 df[col] = pd.to_datetime(df[col]).dt.date
        return df
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return pd.DataFrame()

def add_record(table_name, data_dict):
    try:
        supabase.table(table_name).insert(data_dict).execute()
        st.success(f"✅ Record added to {table_name}!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error adding record: {e}")

def delete_record(table_name, record_id):
    try:
        supabase.table(table_name).delete().eq("id", record_id).execute()
        st.success(f"✅ Record deleted from {table_name}!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error deleting record: {e}")

# --- Specific Update Functions ---
def update_transaction(transaction_id, data_dict):
    try:
        supabase.table("transactions").update(data_dict).eq("id", transaction_id).execute()
        st.success("✅ Transaction updated!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error updating transaction: {e}")

def update_todo_status(todo_id, new_status):
    try:
        supabase.table("todos").update({"is_complete": new_status}).eq("id", todo_id).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error updating To-Do status: {e}")


# ===============================
# PAGE DEFINITIONS
# ===============================
def page_home():
    st.header("🏠 Home Dashboard")
    st.write("Your central hub for a quick overview of everything.")
    
    st.subheader("Financial Summary")
    df = get_all_data("transactions")
    if df.empty:
        st.info("No transactions yet. Add one in the 'Finances' section.")
    else:
        df['amount'] = pd.to_numeric(df['amount'])
        total_income = df[df["type"] == "Income"]["amount"].sum()
        total_expense = df[df["type"] == "Expense"]["amount"].sum()
        net_balance = total_income - total_expense
        num_transactions = len(df)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Income", format_amount(total_income))
        col2.metric("Total Expense", format_amount(total_expense), delta=format_amount(-total_expense))
        col3.metric("Net Balance", format_amount(net_balance))
        col4.metric("Total Transactions", num_transactions)

    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🗓️ Upcoming Dates")
        df_dates = get_all_data("impdates").head(5)
        if not df_dates.empty:
            st.dataframe(df_dates[['event_name', 'event_date']], width='stretch', hide_index=True)
        else:
            st.info("No upcoming dates.")
    with col2:
        st.subheader("⏰ Active Reminders")
        df_reminders = get_all_data("reminders").head(5)
        if not df_reminders.empty:
            st.dataframe(df_reminders[['title', 'reminder_date']], width='stretch', hide_index=True)
        else:
            st.info("No active reminders.")
    with col3:
        st.subheader("✈️ Planned Travel")
        df_travel = get_all_data("travel").head(5)
        if not df_travel.empty:
            st.dataframe(df_travel[['destination', 'start_date']], width='stretch', hide_index=True)
        else:
            st.info("No travel planned.")

# --- FINANCE PAGES ---
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
    
    if st.button("Add Transaction"):
        amount = parse_amount(amount_input)
        if amount > 0:
            data = {"date": date.isoformat(), "person": person, "type": ttype, "category": category, "sub_category": subcategory, "description": desc, "amount": round(amount, 2)}
            add_record("transactions", data)
        else:
            st.warning("Amount must be greater than zero.")

def page_update_transaction():
    st.header("✏️ Update / Delete a Transaction")
    df = get_all_data("transactions")
    if df.empty:
        st.info("No transactions available to update.")
        return

    st.subheader("Recent Transactions")
    st.dataframe(df[['id', 'date', 'person', 'category', 'description', 'amount']].head(20), width='stretch', hide_index=True)
    st.divider()

    transaction_id_to_edit = st.number_input("Enter Transaction ID to Edit/Delete", min_value=1, step=1, value=None)
    if transaction_id_to_edit:
        selected_row_df = df[df['id'] == transaction_id_to_edit]
        if not selected_row_df.empty:
            selected_row = selected_row_df.iloc[0]
            st.subheader(f"Editing Transaction ID: {transaction_id_to_edit}")

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
            
            update_col, delete_col = st.columns(2)
            with update_col:
                if st.button("Update Transaction", key=f"update_btn_{transaction_id_to_edit}"):
                    amount = parse_amount(amount_input)
                    if amount > 0:
                        updated_data = {"date": date.isoformat(), "person": person, "type": ttype, "category": category, "sub_category": subcategory, "description": desc, "amount": round(amount, 2)}
                        update_transaction(transaction_id_to_edit, updated_data)
                        st.rerun()
                    else:
                        st.warning("Amount must be greater than zero.")
            with delete_col:
                if st.button("Delete Transaction", key=f"delete_btn_{transaction_id_to_edit}", type="primary"):
                    delete_record("transactions", transaction_id_to_edit)
                    st.rerun()
        else:
            st.warning("Transaction ID not found.")

def page_view_summary():
    st.header("📊 Expense Summaries")
    df = get_all_data("transactions")
    if df.empty:
        st.info("No transactions to display.")
        return

    df['amount'] = pd.to_numeric(df['amount'])
    persons = ["Pramodh", "Manasa", "Ours"]
    for p in persons:
        st.subheader(f"👤 {p}'s Summary")
        df_person = df[df["person"] == p]
        if df_person.empty:
            st.info(f"No transactions yet for {p}.")
        else:
            total_income = df_person[df_person["type"] == "Income"]["amount"].sum()
            total_expense = df_person[df_person["type"] == "Expense"]["amount"].sum()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Income", format_amount(total_income))
            col2.metric("Total Expense", format_amount(total_expense))
            col3.metric("Balance", format_amount(total_income - total_expense))
        st.divider()

# --- TO-DO PAGE ---
def page_todo():
    st.header("✅ To-Do List")
    with st.expander("➕ Add a new To-Do item", expanded=False):
        with st.form("add_todo_form"):
            item = st.text_input("To-Do Item")
            due_date = st.date_input("Complete by", value=None)
            assigned_user = st.selectbox("Assign to", ["Pramodh", "Manasa", "Ours"])
            submitted = st.form_submit_button("Add To-Do")
            if submitted and item:
                data = {"item": item, "due_date": due_date.isoformat() if due_date else None, "assigned_user": assigned_user}
                add_record("todos", data)
                st.rerun()

    df_todos = get_all_data("todos")
    if not df_todos.empty:
        for index, row in df_todos.iterrows():
            col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
            with col1:
                is_complete = st.checkbox("", value=row['is_complete'], key=f"todo_{row['id']}")
                if is_complete != row['is_complete']:
                    update_todo_status(row['id'], is_complete)
                    st.rerun()
            with col2:
                st.markdown(f"**{row['item']}** (for {row['assigned_user']}) - *Due: {row['due_date'] or 'N/A'}*")
            with col3:
                if st.button("❌", key=f"del_todo_{row['id']}"):
                    delete_record("todos", row['id'])
                    st.rerun()
    else:
        st.info("No to-do items yet.")

# --- REMINDERS PAGE ---
def page_reminders():
    st.header("⏰ Reminders")
    with st.expander("➕ Add a new Reminder", expanded=False):
        with st.form("add_reminder_form"):
            title = st.text_input("Reminder Title")
            reminder_date = st.date_input("Reminder Date")
            assigned_user = st.selectbox("For", ["Pramodh", "Manasa", "Ours"])
            details = st.text_area("Details (optional)")
            submitted = st.form_submit_button("Add Reminder")
            if submitted and title:
                data = {"title": title, "reminder_date": reminder_date.isoformat(), "assigned_user": assigned_user, "details": details}
                add_record("reminders", data)
                st.rerun()
    
    df_reminders = get_all_data("reminders")
    if not df_reminders.empty:
        st.dataframe(df_reminders[['title', 'reminder_date', 'assigned_user', 'details']], width='stretch', hide_index=True)
    else:
        st.info("No reminders yet. Add one above.")

# --- IMPORTANT DATES PAGE ---
def page_important_dates():
    st.header("🗓️ Important Dates")
    with st.expander("➕ Add a new Important Date", expanded=False):
        with st.form("add_impdate_form"):
            event_name = st.text_input("Event Name (e.g., Manasa's Birthday)")
            event_date = st.date_input("Event Date")
            category = st.selectbox("Category", ["Birthday", "Anniversary", "Holiday", "Other"])
            notes = st.text_area("Notes (optional)")
            submitted = st.form_submit_button("Add Date")
            if submitted and event_name:
                data = {"event_name": event_name, "event_date": event_date.isoformat(), "category": category, "notes": notes}
                add_record("impdates", data)
                st.rerun()

    df_impdates = get_all_data("impdates")
    if not df_impdates.empty:
        st.dataframe(df_impdates[['event_name', 'event_date', 'category', 'notes']], width='stretch', hide_index=True)
    else:
        st.info("No important dates yet. Add one above.")

# --- TRAVEL PAGE ---
def page_travel():
    st.header("✈️ Travel Planner")
    with st.expander("➕ Add a new Trip", expanded=False):
        with st.form("add_travel_form"):
            destination = st.text_input("Destination")
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            status = st.selectbox("Status", ["Planned", "Booked", "Completed"])
            notes = st.text_area("Notes (Flight details, hotel, etc.)")
            submitted = st.form_submit_button("Add Trip")
            if submitted and destination:
                if start_date <= end_date:
                    data = {"destination": destination, "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "status": status, "notes": notes}
                    add_record("travel", data)
                    st.rerun()
                else:
                    st.warning("End date must be on or after the start date.")
    
    df_travel = get_all_data("travel")
    if not df_travel.empty:
        st.dataframe(df_travel[['destination', 'start_date', 'end_date', 'status', 'notes']], width='stretch', hide_index=True)
    else:
        st.info("No travel plans yet. Add one above.")


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
    if st.button("🏠 Home", width='stretch'):
        st.session_state.page = "Home"
        st.rerun()

    if st.button("💰 Finances", width='stretch'):
        if not st.session_state.page.startswith("Finances"):
            st.session_state.page = "Finances_Add_Transaction"
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

    if st.button("✅ To-Do", width='stretch'):
        st.session_state.page = "To-Do"
        st.rerun()
    if st.button("⏰ Reminders", width='stretch'):
        st.session_state.page = "Reminders"
        st.rerun()
    if st.button("🗓️ Important Dates", width='stretch'):
        st.session_state.page = "Important Dates"
        st.rerun()
    if st.button("✈️ Travel", width='stretch'):
        st.session_state.page = "Travel"
        st.rerun()

# --- Page Routing ---
page_key = st.session_state.get('page', 'Home')

if page_key == "Home":
    page_home()
elif page_key == "Finances_Add_Transaction":
    page_add_transaction()
elif page_key == "Finances_Update_/_Delete":
    page_update_transaction()
elif page_key == "Finances_View_Summaries":
    page_view_summary()
elif page_key == "To-Do":
    page_todo()
elif page_key == "Reminders":
    page_reminders()
elif page_key == "Important Dates":
    page_important_dates()
elif page_key == "Travel":
    page_travel()
else:
    page_home()

