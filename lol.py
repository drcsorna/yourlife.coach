import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys
import api  # Import the api module
from difflib import SequenceMatcher

# Page configuration
st.set_page_config(page_title="YourLife Coach - Health Journey")

# File paths for meal log, database, and notifications
MEAL_LOG_FILE = "data/meal_log.xlsx"
MEAL_DATABASE_FILE = "data/meal_database.xlsx"
NOTIFICATIONS_FILE = "data/notifications.xlsx"

# Check for required dependencies
try:
    import openpyxl
except ImportError:
    st.error("The 'openpyxl' module is required to save Excel files. Please install it by running 'pip install openpyxl' in your terminal.")
    sys.exit(1)

# Initialize session state variables
if "show_add_popup" not in st.session_state:
    st.session_state.show_add_popup = False
if "show_edit_popup" not in st.session_state:
    st.session_state.show_edit_popup = False
if "meal_to_edit" not in st.session_state:
    st.session_state.meal_to_edit = {}
if "meal_input" not in st.session_state:
    st.session_state.meal_input = ""
if "selected_meal" not in st.session_state:
    st.session_state.selected_meal = ""
if "show_suggestions" not in st.session_state:
    st.session_state.show_suggestions = False
if "show_notifications" not in st.session_state:
    st.session_state.show_notifications = True

# Custom CSS for better styling including proper popup overlay
st.markdown("""
    <style>
    .title-segment {
        font-size: 40px;
        font-weight: bold;
        color: #2c3e50;
    }
    .title-segment:first-child {
        color: #3498db;
    }
    .suggestion-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .suggestion-box:hover {
        background-color: #e9ecef;
        border-color: #3498db;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .suggestion-text {
        font-size: 16px;
        color: #2c3e50;
        margin: 0;
    }
    .suggestion-category {
        font-size: 12px;
        color: #6c757d;
        margin: 0;
    }
    .meal-item {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .meal-info {
        flex-grow: 1;
    }
    .meal-name {
        font-size: 16px;
        font-weight: 500;
        color: #2c3e50;
        margin: 0;
    }
    .meal-category {
        font-size: 14px;
        color: #6c757d;
        margin: 0;
    }
    .action-buttons {
        display: flex;
        gap: 10px;
    }
    .icon-button {
        width: 35px;
        height: 35px;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        transition: all 0.2s ease;
    }
    .edit-button {
        background-color: #3498db;
        color: white;
    }
    .edit-button:hover {
        background-color: #2980b9;
        transform: scale(1.1);
    }
    .delete-button {
        background-color: #e74c3c;
        color: white;
    }
    .delete-button:hover {
        background-color: #c0392b;
        transform: scale(1.1);
    }
    .notification-area {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        max-height: 200px;
        overflow-y: auto;
    }
    .notification-item {
        background-color: white;
        border-left: 4px solid #3498db;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .notification-item.success {
        border-left-color: #27ae60;
    }
    .notification-item.warning {
        border-left-color: #f39c12;
    }
    .notification-item.error {
        border-left-color: #e74c3c;
    }
    .notification-item.info {
        border-left-color: #3498db;
    }
    .notification-text {
        margin: 0;
        font-size: 14px;
        color: #2c3e50;
    }
    .notification-time {
        font-size: 12px;
        color: #6c757d;
        margin: 0;
        margin-top: 5px;
    }
    .popup-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 999;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .popup-content {
        background-color: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        min-width: 400px;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
    }
    .popup-header {
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Function to find fuzzy matches
def find_fuzzy_matches(query, meal_list, threshold=0.4):
    if not query:
        return []
    
    matches = []
    query_lower = query.lower()
    
    for meal in meal_list:
        meal_lower = meal.lower()
        
        # Exact substring match gets highest priority
        if query_lower in meal_lower:
            similarity = 1.0
        else:
            # Use difflib for fuzzy matching
            similarity = SequenceMatcher(None, query_lower, meal_lower).ratio()
        
        if similarity >= threshold:
            matches.append((meal, similarity))
    
    # Sort by similarity score (descending)
    matches.sort(key=lambda x: x[1], reverse=True)
    return [match[0] for match in matches[:8]]  # Return top 8 matches

# Function to load or create notifications
def load_notifications():
    if os.path.exists(NOTIFICATIONS_FILE):
        try:
            return pd.read_excel(NOTIFICATIONS_FILE)
        except Exception as e:
            st.warning(f"Error reading notifications: {e}")
            # Create empty notifications file
            df = pd.DataFrame(columns=["Timestamp", "Type", "Message"])
            df.to_excel(NOTIFICATIONS_FILE, index=False)
            return df
    else:
        # Create empty notifications file
        os.makedirs(os.path.dirname(NOTIFICATIONS_FILE), exist_ok=True)
        df = pd.DataFrame(columns=["Timestamp", "Type", "Message"])
        df.to_excel(NOTIFICATIONS_FILE, index=False)
        return df

# Function to add notification
def add_notification(message, notification_type="info"):
    try:
        notifications = load_notifications()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_notification = pd.DataFrame([[timestamp, notification_type, message]], 
                                      columns=["Timestamp", "Type", "Message"])
        notifications = pd.concat([notifications, new_notification], ignore_index=True)
        notifications.to_excel(NOTIFICATIONS_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Failed to add notification: {e}")
        return False

# Function to initialize database with API data
def initialize_database_with_api():
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Check if database file exists and has content
    database_needs_init = True
    if os.path.exists(MEAL_DATABASE_FILE):
        try:
            existing_df = pd.read_excel(MEAL_DATABASE_FILE)
            if not existing_df.empty and len(existing_df) > 0:
                database_needs_init = False
                add_notification(f"Database already exists with {len(existing_df)} items.", "info")
        except Exception as e:
            st.warning(f"Error reading existing database: {e}")
            database_needs_init = True
    
    if database_needs_init:
        categories = ["Breakfast", "Lunch", "Dinner", "Snack", "Snack"]
        notifications = []
        
        with st.spinner("Initializing database with API data..."):
            try:
                initial_data = api.fetch_api_data(categories, notifications)
                
                if initial_data:
                    df = pd.DataFrame(initial_data, columns=["Meal", "Category"])
                    df.to_excel(MEAL_DATABASE_FILE, index=False)
                    add_notification(f"Database initialized with {len(initial_data)} items from USDA API!", "success")
                else:
                    add_notification("Failed to fetch data from API. Creating empty database.", "error")
                    df = pd.DataFrame(columns=["Meal", "Category"])
                    df.to_excel(MEAL_DATABASE_FILE, index=False)
                    
            except Exception as e:
                add_notification(f"Error initializing database: {e}", "error")
                # Create empty database as fallback
                df = pd.DataFrame(columns=["Meal", "Category"])
                df.to_excel(MEAL_DATABASE_FILE, index=False)
        
        # Display notifications from API
        for msg in notifications:
            add_notification(msg, "success")

# Function to load or create meal log
def load_meal_log():
    if os.path.exists(MEAL_LOG_FILE):
        try:
            return pd.read_excel(MEAL_LOG_FILE)
        except Exception as e:
            st.warning(f"Error reading meal log: {e}")
            # Create empty meal log
            df = pd.DataFrame(columns=["Date", "Category", "Meal", "Quantity"])
            df.to_excel(MEAL_LOG_FILE, index=False)
            return df
    else:
        # Create empty meal log file
        os.makedirs(os.path.dirname(MEAL_LOG_FILE), exist_ok=True)
        df = pd.DataFrame(columns=["Date", "Category", "Meal", "Quantity"])
        df.to_excel(MEAL_LOG_FILE, index=False)
        return df

# Function to load meal database
def load_meal_database():
    if os.path.exists(MEAL_DATABASE_FILE):
        try:
            return pd.read_excel(MEAL_DATABASE_FILE)
        except Exception as e:
            st.error(f"Error reading meal database: {e}")
            return pd.DataFrame(columns=["Meal", "Category"])
    else:
        return pd.DataFrame(columns=["Meal", "Category"])

# Function to save meal to database
def save_meal_to_database(meal_name, category):
    meal_db = load_meal_database()
    if meal_name not in meal_db["Meal"].values:
        new_entry = pd.DataFrame([[meal_name, category]], columns=["Meal", "Category"])
        meal_db = pd.concat([meal_db, new_entry], ignore_index=True)
        meal_db.to_excel(MEAL_DATABASE_FILE, index=False)
        add_notification(f"'{meal_name}' added to database!", "success")
        return True
    return False

# Function to update meal in database
def update_meal_in_database(old_meal_name, new_meal_name, new_category):
    meal_db = load_meal_database()
    if old_meal_name in meal_db["Meal"].values:
        meal_db.loc[meal_db["Meal"] == old_meal_name, "Meal"] = new_meal_name
        meal_db.loc[meal_db["Meal"] == new_meal_name, "Category"] = new_category
        meal_db.to_excel(MEAL_DATABASE_FILE, index=False)
        add_notification(f"Meal '{old_meal_name}' updated to '{new_meal_name}'!", "success")
        return True
    return False

# Function to delete meal from database
def delete_meal_from_database(meal_name):
    meal_db = load_meal_database()
    if meal_name in meal_db["Meal"].values:
        meal_db = meal_db[meal_db["Meal"] != meal_name]
        meal_db.to_excel(MEAL_DATABASE_FILE, index=False)
        add_notification(f"'{meal_name}' deleted from database!", "success")
        return True
    return False

# Initialize database before rendering
initialize_database_with_api()

# Load data
meal_log = load_meal_log()
meal_db = load_meal_database()
notifications = load_notifications()

# Title
st.markdown("""
    <h1>
        <span class="title-segment">your</span><span class="title-segment">LifeCoach</span>
    </h1>
""", unsafe_allow_html=True)
st.subheader("Your Personal Guide to a Healthier You")
st.write("Empower yourself with tools to manage your diet and chronic conditions effectively.")

# Notification area
st.markdown("### 🔔 Notifications")
col_notif, col_toggle = st.columns([4, 1])

with col_toggle:
    if st.button("🔄 Refresh Notifications"):
        st.rerun()

if not notifications.empty:
    # Show notifications area
    notifications_sorted = notifications.sort_values("Timestamp", ascending=False).head(5)  # Show last 5
    
    notification_html = '<div class="notification-area">'
    for _, notif in notifications_sorted.iterrows():
        type_class = notif["Type"] if notif["Type"] in ["success", "warning", "error", "info"] else "info"
        notification_html += f'''
        <div class="notification-item {type_class}">
            <p class="notification-text">{notif["Message"]}</p>
            <p class="notification-time">{notif["Timestamp"]}</p>
        </div>
        '''
    notification_html += '</div>'
    
    st.markdown(notification_html, unsafe_allow_html=True)
    
    # Show/hide toggle for older notifications
    if len(notifications) > 5:
        with st.expander(f"📋 Show all {len(notifications)} notifications"):
            st.dataframe(notifications.sort_values("Timestamp", ascending=False), use_container_width=True)
else:
    st.info("🔔 No notifications yet.")

# Meal logging section
st.header("Log Your Meal")

# Get list of meals for autocomplete
meal_options = meal_db["Meal"].tolist() if not meal_db.empty else []
meal_categories = dict(zip(meal_db["Meal"], meal_db["Category"])) if not meal_db.empty else {}

col1, col2 = st.columns(2)

with col1:
    # Custom autocomplete input
    meal_input = st.text_input("Start typing meal name...", 
                              value=st.session_state.selected_meal, 
                              key="meal_input_field",
                              placeholder="e.g., Grilled Chicken, Oatmeal, Apple...")
    
    # Show suggestions if there's input
    if meal_input and meal_input != st.session_state.selected_meal:
        matches = find_fuzzy_matches(meal_input, meal_options)
        
        if matches:
            st.markdown("**Suggestions:**")
            for match in matches:
                category = meal_categories.get(match, "Unknown")
                # Create clickable suggestion
                suggestion_html = f"""
                <div class="suggestion-box" onclick="
                    document.querySelector('[data-testid=\\'textinput-textarea\\']').value='{match}';
                    document.querySelector('[data-testid=\\'textinput-textarea\\']').dispatchEvent(new Event('input', {{bubbles: true}}));
                ">
                    <p class="suggestion-text">{match}</p>
                    <p class="suggestion-category">{category}</p>
                </div>
                """
                st.markdown(suggestion_html, unsafe_allow_html=True)
                
                # Create invisible button for each suggestion to handle clicks
                if st.button(f"Select {match}", key=f"select_{match}", help="Click to select this meal"):
                    st.session_state.selected_meal = match
                    st.rerun()
        else:
            st.info("💡 No matches found. You can add this as a new meal!")

with col2:
    category = st.selectbox("Category", ["Breakfast", "Lunch", "Dinner", "Snack1", "Snack2"], key="meal_category")

with col1:
    quantity = st.number_input("Quantity (e.g., servings)", step=0.1, min_value=0.0)

# Use the selected meal or current input
meal = st.session_state.selected_meal if st.session_state.selected_meal else meal_input

# Check if meal exists in database
meal_exists_in_db = meal in meal_options if meal else False

if meal and not meal_exists_in_db:
    st.warning(f"'{meal}' is not in your meal database.")
    if st.button("➕ Add to Database", key="add_to_db_btn"):
        st.session_state.show_add_popup = True
        st.session_state.new_meal_name = meal
        st.session_state.new_meal_category = category

col_save, col_space = st.columns([1, 3])
with col_save:
    save_meal_btn = st.button("💾 Save Meal", type="primary")

if save_meal_btn:
    if not meal:
        st.error("Please enter or select a meal name.")
        add_notification("Failed to save meal: No meal name provided", "error")
    elif quantity <= 0:
        st.error("Please enter a valid quantity greater than 0.")
        add_notification("Failed to save meal: Invalid quantity", "error")
    else:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            new_entry = pd.DataFrame([[date, category, meal, quantity]], columns=["Date", "Category", "Meal", "Quantity"])
            meal_log = pd.concat([meal_log, new_entry], ignore_index=True)
            meal_log.to_excel(MEAL_LOG_FILE, index=False)
            st.success("✅ Meal saved successfully!")
            add_notification(f"Meal saved: {meal} ({quantity} servings)", "success")
            
            # Clear selection
            st.session_state.selected_meal = ""
            
            # If meal doesn't exist in database, suggest adding it
            if not meal_exists_in_db:
                st.info("💡 Consider adding this meal to your database for future quick selection.")
                
        except Exception as e:
            st.error(f"Failed to save meal: {e}")
            add_notification(f"Failed to save meal: {e}", "error")

# Popup overlays
popup_html = ""

# Add Meal to Database Popup
if st.session_state.show_add_popup:
    popup_html += '''
    <div class="popup-backdrop" id="add-popup">
        <div class="popup-content">
            <div class="popup-header">
                ➕ Add Meal to Database
            </div>
        </div>
    </div>
    '''

# Edit Meal Popup
if st.session_state.show_edit_popup:
    popup_html += '''
    <div class="popup-backdrop" id="edit-popup">
        <div class="popup-content">
            <div class="popup-header">
                ✏️ Edit Meal
            </div>
        </div>
    </div>
    '''

if popup_html:
    st.markdown(popup_html, unsafe_allow_html=True)

# Add Meal to Database Popup Content
if st.session_state.show_add_popup:
    with st.container():
        st.markdown("---")
        st.markdown("### ➕ Add Meal to Database")
        
        col1, col2 = st.columns(2)
        with col1:
            popup_meal_name = st.text_input("Meal Name", value=st.session_state.get("new_meal_name", ""), key="popup_meal_name")
        with col2:
            popup_category = st.selectbox("Category", ["Breakfast", "Lunch", "Dinner", "Snack1", "Snack2"], 
                                        index=["Breakfast", "Lunch", "Dinner", "Snack1", "Snack2"].index(st.session_state.get("new_meal_category", "Breakfast")),
                                        key="popup_category")
        
        col_add, col_cancel = st.columns(2)
        with col_add:
            if st.button("✅ Add to Database", key="confirm_add"):
                if popup_meal_name:
                    if save_meal_to_database(popup_meal_name, popup_category):
                        st.success(f"✅ '{popup_meal_name}' added to database!")
                        st.session_state.show_add_popup = False
                        st.rerun()
                    else:
                        st.warning("⚠️ Meal already exists in database.")
                        add_notification(f"Meal '{popup_meal_name}' already exists in database", "warning")
                else:
                    st.error("Please enter a meal name.")
        
        with col_cancel:
            if st.button("❌ Cancel", key="cancel_add"):
                st.session_state.show_add_popup = False
                st.rerun()

# Edit Meal Popup Content
if st.session_state.show_edit_popup:
    with st.container():
        st.markdown("---")
        st.markdown("### ✏️ Edit Meal")
        
        col1, col2 = st.columns(2)
        with col1:
            edit_meal_name = st.text_input("Meal Name", value=st.session_state.meal_to_edit.get("meal", ""), key="edit_meal_name")
        with col2:
            current_category = st.session_state.meal_to_edit.get("category", "Breakfast")
            category_options = ["Breakfast", "Lunch", "Dinner", "Snack1", "Snack2"]
            category_index = category_options.index(current_category) if current_category in category_options else 0
            edit_category = st.selectbox("Category", category_options, index=category_index, key="edit_category")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("💾 Save Changes", key="confirm_edit"):
                if edit_meal_name:
                    old_meal_name = st.session_state.meal_to_edit.get("meal", "")
                    if update_meal_in_database(old_meal_name, edit_meal_name, edit_category):
                        st.success(f"✅ Meal updated successfully!")
                        st.session_state.show_edit_popup = False
                        st.session_state.meal_to_edit = {}
                        st.rerun()
                    else:
                        st.error("❌ Failed to update meal.")
                        add_notification(f"Failed to update meal '{old_meal_name}'", "error")
                else:
                    st.error("Please enter a meal name.")
        
        with col_cancel:
            if st.button("❌ Cancel", key="cancel_edit"):
                st.session_state.show_edit_popup = False
                st.session_state.meal_to_edit = {}
                st.rerun()

# Database management section
st.header("🗄️ Meal Database")

# Add button to manually refresh database
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Refresh"):
        st.rerun()

# Show database content
if meal_db.empty:
    st.warning("No meals in the database. The API may have failed to provide data or there was an issue with initialization.")
    if st.button("🔄 Try Initialize Database Again"):
        # Force re-initialization
        if os.path.exists(MEAL_DATABASE_FILE):
            os.remove(MEAL_DATABASE_FILE)
        add_notification("Attempting to reinitialize database...", "info")
        st.rerun()
else:
    st.success(f"📊 Database contains {len(meal_db)} meals")
    
    # Display database with styled items and icon buttons
    st.markdown("### Manage Database Items")
    
    for idx, row in meal_db.iterrows():
        # Create styled meal item
        meal_item_html = f"""
        <div class="meal-item">
            <div class="meal-info">
                <p class="meal-name">{row['Meal']}</p>
                <p class="meal-category">{row['Category']}</p>
            </div>
        </div>
        """
        
        col1, col2, col3 = st.columns([6, 1, 1])
        
        with col1:
            st.markdown(meal_item_html, unsafe_allow_html=True)
        
        with col2:
            if st.button("✏️", key=f"edit_{idx}", help="Edit meal"):
                st.session_state.show_edit_popup = True
                st.session_state.meal_to_edit = {"meal": row["Meal"], "category": row["Category"]}
                st.rerun()
        
        with col3:
            if st.button("🗑️", key=f"delete_{idx}", help="Delete meal"):
                if delete_meal_from_database(row["Meal"]):
                    st.success(f"✅ '{row['Meal']}' deleted successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to delete meal.")
                    add_notification(f"Failed to delete meal '{row['Meal']}'", "error")

# Display recent meal logs
st.header("📝 Recent Meal Logs")
if not meal_log.empty:
    # Show last 10 entries
    recent_logs = meal_log.tail(10).sort_values("Date", ascending=False)
    st.dataframe(recent_logs, use_container_width=True)
else:
    st.info("📝 No meal logs recorded yet.")

# Debug information
with st.expander("🔧 Debug Information"):
    st.write(f"Meal database file exists: {os.path.exists(MEAL_DATABASE_FILE)}")
    st.write(f"Meal log file exists: {os.path.exists(MEAL_LOG_FILE)}")
    st.write(f"Notifications file exists: {os.path.exists(NOTIFICATIONS_FILE)}")
    if os.path.exists(MEAL_DATABASE_FILE):
        st.write(f"Database file size: {os.path.getsize(MEAL_DATABASE_FILE)} bytes")
    st.write(f"Current meal database shape: {meal_db.shape}")
    st.write(f"Current meal log shape: {meal_log.shape}")
    st.write(f"Current notifications shape: {notifications.shape}")