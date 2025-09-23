import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
import plotly.express as px
import calendar
import time

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
    """Returns `True` if the user is authenticated, `False` otherwise."""
    # 1. Check if user is already authenticated and session is not expired
    if st.session_state.get("authenticated", False):
        # Check for session timeout (1 hour = 3600 seconds)
        if time.time() - st.session_state.get("login_time", 0) > 3600:
            # Clear all session state keys if expired
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.warning("Your session has expired. Please log in again.")
            st.rerun()
        else:
            return True # Session is active and valid

    # 2. If not authenticated, show the login form
    st.title("Welcome Pramodh & Manasa")
    st.write("")
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                # Check if the username and password are correct
                if st.session_state.get("username") in st.secrets["credentials"]["usernames"] and \
                   st.secrets["credentials"]["usernames"][st.session_state.get("username")] == st.session_state.get("password"):
                    
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = st.session_state.get("username")
                    st.session_state["login_time"] = time.time()  # Store login time
                    
                    # Clean up credentials from session state
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
@st.cache_data(ttl=300)
def get_all_data(table_name):
    try:
        response = supabase.table(table_name).select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(response.data)
        for col in ['date', 'due_date', 'reminder_date', 'event_date', 'start_date', 'end_date']:
             if col in df.columns:
                 df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
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

def update_record(table_name, record_id, data_dict):
    try:
        supabase.table(table_name).update(data_dict).eq("id", record_id).execute()
        st.success(f"✅ Record updated in {table_name}!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error updating record: {e}")

def delete_record(table_name, record_id):
    try:
        supabase.table(table_name).delete().eq("id", record_id).execute()
        st.success(f"✅ Record deleted from {table_name}!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error deleting record: {e}")

def update_todo_status(todo_id, new_status):
    try:
        supabase.table("todos").update({"is_complete": new_status}).eq("id", todo_id).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error updating To-Do status: {e}")

# ===============================
# HELPER FUNCTIONS FOR HOME PAGE
# ===============================
def get_relativedelta_text(start_date, end_date):
    """Calculates years, months, days between two dates and returns a formatted string."""
    if start_date > end_date:
        return "In the past"

    years = end_date.year - start_date.year
    months = end_date.month - start_date.month
    days = end_date.day - start_date.day

    if days < 0:
        months -= 1
        prev_month_year = end_date.year if end_date.month > 1 else end_date.year - 1
        prev_month = end_date.month - 1 if end_date.month > 1 else 12
        days += calendar.monthrange(prev_month_year, prev_month)[1]
    
    if months < 0:
        years -= 1
        months += 12
    
    parts = []
    if years > 0: parts.append(f"{years}y")
    if months > 0: parts.append(f"{months}m")
    if days > 0 or not parts: parts.append(f"{days}d")
        
    return ", ".join(parts)

def calculate_anniversary_details(event_date):
    """Calculates age and time to next anniversary for a given date."""
    if pd.isnull(event_date):
        return None, None

    today = datetime.date.today()
    if not isinstance(event_date, datetime.date):
        event_date = pd.to_datetime(event_date).date()

    # 1. Time passed since original event
    time_passed_str = get_relativedelta_text(event_date, today)

    # 2. Find next occurrence
    next_occurrence_year = today.year
    if (today.month, today.day) > (event_date.month, event_date.day):
        next_occurrence_year += 1
    
    try:
        next_event_date = event_date.replace(year=next_occurrence_year)
    except ValueError: # Handle Feb 29 on non-leap years
        next_event_date = datetime.date(next_occurrence_year, 2, 28)

    # 3. Time until next occurrence
    if next_event_date == today:
        time_to_next_str = "🎉 Today!"
    else:
        time_to_next_str = get_relativedelta_text(today, next_event_date)
        
    return time_passed_str, time_to_next_str

# ===============================
# PAGE DEFINITIONS
# ===============================
def page_home():
    st.header("🏠 Home Dashboard")
    st.write("Your central hub for a quick overview of everything.")
    
    # --- Financial Summary with Shortcut ---
    col_title, col_button = st.columns([0.8, 0.2])
    with col_title:
        st.subheader("Financial Summary")
    with col_button:
        if st.button("➕ Add Transaction", use_container_width=True):
            st.session_state.page = "Finances_Add_Transaction"
            st.rerun()

    df = get_all_data("transactions")
    if df.empty:
        st.info("No transactions yet. Click the button above to add one.")
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
    
    # --- Dashboard Cards ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🗓️ Important Dates")
        df_dates = get_all_data("impdates").head(5)
        
        if not df_dates.empty:
            display_df_data = []
            for index, row in df_dates.iterrows():
                passed_str, next_str = calculate_anniversary_details(row['event_date'])
                if passed_str and next_str:
                    display_df_data.append({
                        "Event": f"{row['event_name']} ({row['category']})",
                        "Passed": passed_str,
                        "Next In": next_str
                    })
            
            if display_df_data:
                display_df = pd.DataFrame(display_df_data)
                st.dataframe(display_df, hide_index=True, use_container_width=True)
        else:
            st.info("No important dates.")
            
    with col2:
        st.subheader("✅ Upcoming To-Dos")
        df_todos = get_all_data("todos")
        upcoming_todos = df_todos[df_todos['is_complete'] == False].sort_values(by="due_date").head(5)
        if not upcoming_todos.empty:
            st.dataframe(upcoming_todos[['item', 'due_date', 'assigned_user']], use_container_width=True, hide_index=True)
        else:
            st.info("No upcoming to-do items.")
            
    with col3:
        st.subheader("✈️ Planned Travel")
        df_travel = get_all_data("travel").head(5)
        if not df_travel.empty:
            st.dataframe(df_travel[['destination', 'start_date']], use_container_width=True, hide_index=True)
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
        category = st.selectbox("Category", categories, key="add_category")
        
        subcategory = None
        if category != "Others":
            subcategories = CATEGORY_MAP.get(ttype, {}).get(category, ["-"])
            subcategory = st.selectbox("Sub-Category", subcategories, key="add_subcategory")

        desc_label = "Description (Mandatory for 'Others')" if category == "Others" else "Description"
        desc = st.text_input(desc_label)
        amount_input = st.text_input("Amount", "0")
    
    if st.button("Add Transaction"):
        if category == "Others" and not desc:
            st.warning("Description is mandatory when 'Others' category is selected.")
        else:
            amount = parse_amount(amount_input)
            if amount > 0:
                final_subcategory = desc if category == "Others" else subcategory
                data = {
                    "date": date.isoformat(), "person": person, "type": ttype, 
                    "category": category, "sub_category": final_subcategory, 
                    "description": desc, "amount": round(amount, 2)
                }
                add_record("transactions", data)
                st.rerun()
            else:
                st.warning("Amount must be greater than zero.")

def page_update_transaction():
    st.header("✏️ Update / Delete Transaction")
    df = get_all_data("transactions")
    if df.empty:
        st.info("No transactions available.")
        return

    st.dataframe(df[['id', 'date', 'person', 'category', 'description', 'amount']].head(20), use_container_width=True, hide_index=True)
    st.divider()

    transaction_id = st.number_input("Enter Transaction ID to Edit/Delete", min_value=1, step=1, value=None)
    if transaction_id:
        selected_row = df[df['id'] == transaction_id]
        if not selected_row.empty:
            item = selected_row.iloc[0]
            st.subheader(f"Editing Transaction ID: {transaction_id}")
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date", value=item['date'], key=f"date_{transaction_id}")
                person = st.selectbox("Person", ["Pramodh", "Manasa", "Ours"], index=["Pramodh", "Manasa", "Ours"].index(item['person']), key=f"person_{transaction_id}")
                ttype = st.selectbox("Type", ["Expense", "Income"], index=["Expense", "Income"].index(item['type']), key=f"type_{transaction_id}")
            with col2:
                categories = list(CATEGORY_MAP.get(ttype, {}).keys())
                cat_index = categories.index(item['category']) if item['category'] in categories else 0
                category = st.selectbox("Category", categories, index=cat_index, key=f"cat_{transaction_id}")
                
                subcategory = item['sub_category']
                if category != "Others":
                    subcategories = CATEGORY_MAP.get(ttype, {}).get(category, ["-"])
                    sub_cat_index = subcategories.index(item['sub_category']) if item['sub_category'] in subcategories else 0
                    subcategory = st.selectbox("Sub-Category", subcategories, index=sub_cat_index, key=f"subcat_{transaction_id}")

                desc_label = "Description (Mandatory for 'Others')" if category == "Others" else "Description"
                desc = st.text_input(desc_label, value=item['description'], key=f"desc_{transaction_id}")
                amount_input = st.text_input("Amount", value=str(item['amount']), key=f"amount_{transaction_id}")
            
            update_col, delete_col = st.columns(2)
            with update_col:
                if st.button("Update Transaction", key=f"upd_btn_{transaction_id}"):
                    if category == "Others" and not desc:
                        st.warning("Description is mandatory when 'Others' category is selected.")
                    else:
                        amount = parse_amount(amount_input)
                        if amount > 0:
                            final_subcategory = desc if category == "Others" else subcategory
                            data = {
                                "date": date.isoformat(), "person": person, "type": ttype, 
                                "category": category, "sub_category": final_subcategory, 
                                "description": desc, "amount": round(amount, 2)
                            }
                            update_record("transactions", transaction_id, data)
                            st.rerun()
                        else:
                            st.warning("Amount must be greater than zero.")
            with delete_col:
                if st.button("Delete Transaction", key=f"del_btn_{transaction_id}", type="primary"):
                    delete_record("transactions", transaction_id)
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
            
            # ROW 1: Metrics
            metric_cols = st.columns(3)
            metric_cols[0].metric("Total Income", format_amount(total_income))
            metric_cols[1].metric("Total Expense", format_amount(total_expense))
            metric_cols[2].metric("Balance", format_amount(total_income - total_expense))
            
            # ROW 2: Chart and Table
            df_expense = df_person[df_person["type"] == "Expense"]
            if not df_expense.empty:
                chart_col, table_col = st.columns([0.4, 0.6])
                
                with chart_col:
                    expense_by_cat = df_expense.groupby('category')['amount'].sum().reset_index()
                    fig = px.pie(expense_by_cat, names='category', values='amount', title='Expense by Category',
                                 hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                    fig.update_layout(showlegend=False, height=300, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                
                with table_col:
                    st.write("**Expense Details**")
                    expense_details = df_expense.groupby(['category', 'sub_category'])['amount'].sum().reset_index().sort_values(by='amount', ascending=False)
                    expense_details['Amount'] = expense_details['amount'].apply(format_amount)
                    st.dataframe(
                        expense_details[['category', 'sub_category', 'Amount']],
                        hide_index=True,
                        use_container_width=True
                    )
            else:
                 st.info("No expenses recorded for this person.")

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

# --- REMINDERS PAGES ---
def page_add_reminder():
    st.header("⏰ Add New Reminder")
    with st.form("add_reminder_form"):
        title = st.text_input("Reminder Title")
        reminder_date = st.date_input("Reminder Date")
        assigned_user = st.selectbox("For", ["Pramodh", "Manasa", "Ours"])
        details = st.text_area("Details (optional)")
        submitted = st.form_submit_button("Add Reminder")
        if submitted and title:
            data = {"title": title, "reminder_date": reminder_date.isoformat(), "assigned_user": assigned_user, "details": details}
            add_record("reminders", data)
            st.session_state.page = "Reminders_View_&_Edit"
            st.rerun()

def page_view_reminders():
    st.header("⏰ View & Edit Reminders")
    df = get_all_data("reminders")
    if df.empty:
        st.info("No reminders available. Add one to get started.")
        return

    st.dataframe(df[['id', 'title', 'reminder_date', 'assigned_user']], use_container_width=True, hide_index=True)
    st.divider()

    item_id = st.number_input("Enter Reminder ID to Edit/Delete", min_value=1, step=1, value=None)
    if item_id:
        selected_item = df[df['id'] == item_id]
        if not selected_item.empty:
            item = selected_item.iloc[0]
            st.subheader(f"Editing Reminder ID: {item_id}")
            title = st.text_input("Title", value=item['title'])
            reminder_date = st.date_input("Date", value=item['reminder_date'])
            assigned_user = st.selectbox("For", ["Pramodh", "Manasa", "Ours"], index=["Pramodh", "Manasa", "Ours"].index(item['assigned_user']))
            details = st.text_area("Details", value=item['details'])
            
            update_col, delete_col = st.columns(2)
            with update_col:
                if st.button("Update Reminder"):
                    data = {"title": title, "reminder_date": reminder_date.isoformat(), "assigned_user": assigned_user, "details": details}
                    update_record("reminders", item_id, data)
                    st.rerun()
            with delete_col:
                if st.button("Delete Reminder", type="primary"):
                    delete_record("reminders", item_id)
                    st.rerun()
        else:
            st.warning("Reminder ID not found.")

# --- IMPORTANT DATES PAGES ---
def page_add_impdate():
    st.header("🗓️ Add Important Date")
    with st.form("add_impdate_form"):
        event_name = st.text_input("Event Name (e.g., Manasa's Birthday)")
        event_date = st.date_input("Event Date")
        category = st.selectbox("Category", ["Birthday", "Anniversary", "Holiday", "Other"])
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Add Date")
        if submitted and event_name:
            data = {"event_name": event_name, "event_date": event_date.isoformat(), "category": category, "notes": notes}
            add_record("impdates", data)
            st.session_state.page = "Important_Dates_View_&_Edit"
            st.rerun()
            
def page_view_impdates():
    st.header("🗓️ View & Edit Important Dates")
    df = get_all_data("impdates")
    if df.empty:
        st.info("No dates available.")
        return
        
    st.dataframe(df[['id', 'event_name', 'event_date', 'category']], use_container_width=True, hide_index=True)
    st.divider()
    
    item_id = st.number_input("Enter Date ID to Edit/Delete", min_value=1, step=1, value=None)
    if item_id:
        selected_item = df[df['id'] == item_id]
        if not selected_item.empty:
            item = selected_item.iloc[0]
            st.subheader(f"Editing Date ID: {item_id}")
            event_name = st.text_input("Event Name", value=item['event_name'])
            event_date = st.date_input("Event Date", value=item['event_date'])
            category = st.selectbox("Category", ["Birthday", "Anniversary", "Holiday", "Other"], index=["Birthday", "Anniversary", "Holiday", "Other"].index(item['category']))
            notes = st.text_area("Notes", value=item['notes'])
            
            update_col, delete_col = st.columns(2)
            with update_col:
                if st.button("Update Date"):
                    data = {"event_name": event_name, "event_date": event_date.isoformat(), "category": category, "notes": notes}
                    update_record("impdates", item_id, data)
                    st.rerun()
            with delete_col:
                if st.button("Delete Date", type="primary"):
                    delete_record("impdates", item_id)
                    st.rerun()
        else:
            st.warning("Date ID not found.")

# --- TRAVEL PAGES ---
def page_add_travel():
    st.header("✈️ Add New Trip")
    with st.form("add_travel_form"):
        destination = st.text_input("Destination")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        status = st.selectbox("Status", ["Planned", "Booked", "Completed"])
        budget = st.number_input("Budget (Optional)", min_value=0.0, format="%.2f")
        notes = st.text_area("Notes (Flight details, hotel, etc.)")
        submitted = st.form_submit_button("Add Trip")
        if submitted and destination:
            if start_date <= end_date:
                data = {"destination": destination, "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "status": status, "budget": budget, "notes": notes}
                add_record("travel", data)
                st.session_state.page = "Travel_View_&_Edit"
                st.rerun()
            else:
                st.warning("End date must be on or after the start date.")

def page_view_travel():
    st.header("✈️ View & Edit Trips")
    df = get_all_data("travel")
    if df.empty:
        st.info("No travel plans available.")
        return

    st.dataframe(df[['id', 'destination', 'start_date', 'end_date', 'status', 'budget']], use_container_width=True, hide_index=True)
    st.divider()

    item_id = st.number_input("Enter Trip ID to Edit/Delete", min_value=1, step=1, value=None)
    if item_id:
        selected_item = df[df['id'] == item_id]
        if not selected_item.empty:
            item = selected_item.iloc[0]
            st.subheader(f"Editing Trip ID: {item_id}")
            destination = st.text_input("Destination", value=item['destination'])
            start_date = st.date_input("Start Date", value=item['start_date'])
            end_date = st.date_input("End Date", value=item['end_date'])
            status = st.selectbox("Status", ["Planned", "Booked", "Completed"], index=["Planned", "Booked", "Completed"].index(item['status']))
            budget = st.number_input("Budget", value=float(item.get('budget', 0.0)), format="%.2f")
            notes = st.text_area("Notes", value=item['notes'])
            
            update_col, delete_col = st.columns(2)
            with update_col:
                if st.button("Update Trip"):
                    data = {"destination": destination, "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "status": status, "budget": budget, "notes": notes}
                    update_record("travel", item_id, data)
                    st.rerun()
            with delete_col:
                if st.button("Delete Trip", type="primary"):
                    delete_record("travel", item_id)
                    st.rerun()
        else:
            st.warning("Trip ID not found.")

# ===============================
# MAIN APP UI & NAVIGATION
# ===============================
def create_sidebar_nav():
    st.sidebar.title("App Sections")
    
    pages = {
        "Home": "🏠 Home",
        "Finances": "💰 Finances",
        "To-Do": "✅ To-Do",
        "Reminders": "⏰ Reminders",
        "Important Dates": "🗓️ Important Dates",
        "Travel": "✈️ Travel"
    }
    
    sub_pages = {
        "Finances": ["Add Transaction", "Update / Delete", "View Summaries"],
        "Reminders": ["View & Edit", "Add New"],
        "Important Dates": ["View & Edit", "Add New"],
        "Travel": ["View & Edit", "Add New"]
    }

    if 'page' not in st.session_state:
        st.session_state.page = "Home"

    for page, label in pages.items():
        if st.sidebar.button(label, use_container_width=True):
            if page in sub_pages:
                st.session_state.page = f"{page.replace(' ', '_')}_{sub_pages[page][0].replace(' ', '_')}"
            else:
                st.session_state.page = page
            st.rerun()

        if st.session_state.page.startswith(page.replace(' ', '_')) and page in sub_pages:
            try:
                current_sub_page = st.session_state.page.split(f"{page.replace(' ', '_')}_")[1].replace("_", " ")
                current_index = sub_pages[page].index(current_sub_page)
            except (ValueError, IndexError):
                current_index = 0
            
            selected_sub_page = st.sidebar.radio(
                f"{page} Menu", sub_pages[page], index=current_index, label_visibility="collapsed"
            )
            
            new_page_state = f"{page.replace(' ', '_')}_{selected_sub_page.replace(' ', '_')}"
            if st.session_state.page != new_page_state:
                st.session_state.page = new_page_state
                st.rerun()

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

create_sidebar_nav()

# --- Page Routing ---
page_key = st.session_state.get('page', 'Home')
if page_key == "Home": page_home()
elif page_key == "Finances_Add_Transaction": page_add_transaction()
elif page_key == "Finances_Update_/_Delete": page_update_transaction()
elif page_key == "Finances_View_Summaries": page_view_summary()
elif page_key == "To-Do": page_todo()
elif page_key == "Reminders_View_&_Edit": page_view_reminders()
elif page_key == "Reminders_Add_New": page_add_reminder()
elif page_key == "Important_Dates_View_&_Edit": page_view_impdates()
elif page_key == "Important_Dates_Add_New": page_add_impdate()
elif page_key == "Travel_View_&_Edit": page_view_travel()
elif page_key == "Travel_Add_New": page_add_travel()
else: page_home()

