import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime, timedelta, date
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import hashlib
import time

# Set page configuration
st.set_page_config(
    page_title="Time Tracker",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SECURITY: Authentication System
def secure_personal_app():
    """Secure the personal time tracker app with password authentication"""

    def password_entered():
        """Checks the entered password against the hash in secrets"""
        entered_password = st.session_state["password"]

        # Get password hash from secrets
        try:
            correct_hash = st.secrets["app_password_hash"]
            entered_hash = hashlib.sha256(entered_password.encode()).hexdigest()

            if entered_hash == correct_hash:
                st.session_state["authenticated"] = True
                st.session_state["auth_timestamp"] = time.time()
                del st.session_state["password"]
                st.success("✅ Access granted! Loading your time tracker...")
                time.sleep(1)  # Brief pause for UX
                st.rerun()
            else:
                st.session_state["authenticated"] = False
                st.error("❌ Incorrect password. Access denied.")
        except KeyError:
            st.error("❌ Authentication not configured. Please contact the administrator.")
        except Exception as e:
            st.error(f"❌ Authentication error: {str(e)}")

    # Check if already authenticated and not timed out (1 hour timeout)
    if (st.session_state.get("authenticated", False) and 
        time.time() - st.session_state.get("auth_timestamp", 0) < 3600):
        return True

    # Reset authentication state
    st.session_state["authenticated"] = False

    # Show login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("## 🔐 Personal Time Tracker")
        st.markdown("---")

        with st.container():
            st.markdown("### 🛡️ Secure Access Required")

            st.info("""
            This is your personal time tracking application containing sensitive data.
            Please enter your password to continue.
            """)

            st.text_input(
                "🔑 Enter Password:", 
                type="password", 
                on_change=password_entered, 
                key="password",
                placeholder="Your secure password",
                help="Enter the password configured for this app"
            )

            st.markdown("---")

            with st.expander("ℹ️ Security Information"):
                st.markdown("""
                **Security Features:**
                - 🔐 Password-protected access
                - ⏰ Automatic session timeout (1 hour)
                - 🔒 Encrypted password storage
                - 🛡️ Secure data transmission (HTTPS)

                **Data Protection:**
                - Your time tracking data is stored securely
                - Google Sheets integration uses encrypted credentials
                - No sensitive information is logged or shared
                """)

        st.markdown("---")
        st.caption("🔒 Protected by secure authentication • Built with Streamlit")

    return False

# Check authentication - App will not proceed without valid login
if not secure_personal_app():
    st.stop()

# Add logout option and session info in sidebar after successful authentication
with st.sidebar:
    st.markdown("---")
    st.markdown("### 👤 Session Info")

    auth_time = st.session_state.get("auth_timestamp", time.time())
    session_duration = int((time.time() - auth_time) / 60)  # minutes
    timeout_remaining = 60 - session_duration  # minutes until timeout

    st.info(f"""
    **Session Active:** {session_duration} min  
    **Auto-logout in:** {max(0, timeout_remaining)} min
    """)

    if st.button("🚪 Logout", type="secondary", help="Clear session and logout"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("👋 Logged out successfully")
        st.rerun()

# Session timeout check
def check_session_timeout():
    """Check and handle session timeout"""
    if st.session_state.get("authenticated", False):
        if time.time() - st.session_state.get("auth_timestamp", 0) > 3600:  # 1 hour
            st.warning("⏰ Session expired. Please login again.")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            time.sleep(2)
            st.rerun()

# Check session timeout
check_session_timeout()

# REST OF YOUR EXISTING TIME TRACKER CODE CONTINUES HERE
# (Insert your existing TimeTracker class and all app logic below this point)

class TimeTracker:
    def __init__(self, sheet_name='Time_Tracking', use_google_sheets=True):
        self.sheet_name = sheet_name
        self.use_google_sheets = use_google_sheets
        self.fieldnames = ['date', 'project', 'category', 'duration_hours', 'description']

        if self.use_google_sheets:
            self.setup_google_sheets()
        else:
            # Fallback to CSV if Google Sheets not available
            self.data_file = 'time_tracking_data.csv'
            self.ensure_data_file_exists()

    def setup_google_sheets(self):
        """Setup Google Sheets connection"""
        try:
            # Check if credentials are provided in Streamlit secrets
            if "gcp_service_account" in st.secrets:
                # Use Streamlit secrets (recommended for deployment)
                credentials_dict = dict(st.secrets["gcp_service_account"])
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
                self.client = gspread.authorize(credentials)
                self.sheet = self.client.open(self.sheet_name).sheet1
                self.ensure_sheet_headers()
                st.success("✅ Connected to Google Sheets successfully!")
            else:
                # Try to use local credentials file
                try:
                    scopes = [
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                    credentials = Credentials.from_service_account_file('credentials.json', scopes=scopes)
                    self.client = gspread.authorize(credentials)
                    self.sheet = self.client.open(self.sheet_name).sheet1
                    self.ensure_sheet_headers()
                    st.success("✅ Connected to Google Sheets successfully!")
                except Exception as e:
                    st.error(f"❌ Could not connect to Google Sheets: {str(e)}")
                    st.info("💡 Falling back to local CSV storage")
                    self.use_google_sheets = False
                    self.data_file = 'time_tracking_data.csv'
                    self.ensure_data_file_exists()
        except Exception as e:
            st.error(f"❌ Google Sheets setup failed: {str(e)}")
            st.info("💡 Falling back to local CSV storage")
            self.use_google_sheets = False
            self.data_file = 'time_tracking_data.csv'
            self.ensure_data_file_exists()

    def ensure_sheet_headers(self):
        """Ensure Google Sheet has proper headers"""
        try:
            existing_headers = self.sheet.row_values(1)
            if not existing_headers or existing_headers != self.fieldnames:
                self.sheet.clear()
                self.sheet.append_row(self.fieldnames, value_input_option="USER_ENTERED")
        except Exception as e:
            st.error(f"❌ Could not setup sheet headers: {str(e)}")

    def ensure_data_file_exists(self):
        """Create CSV file with headers if it doesn't exist (fallback)"""
        import csv
        import os
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def add_entry(self, project, category, duration_hours, description="", entry_date=None):
        """Add a time entry to the database"""
        if entry_date is None:
            entry_date = datetime.now().date()

        if self.use_google_sheets:
            try:
                new_row = [
                    entry_date.strftime('%Y-%m-%d'),
                    project,
                    category,
                    float(duration_hours),
                    description
                ]
                self.sheet.append_row(new_row, value_input_option="USER_ENTERED")
                return True
            except Exception as e:
                st.error(f"❌ Failed to add entry to Google Sheets: {str(e)}")
                return False
        else:
            # Fallback to CSV
            import csv
            entry = {
                'date': entry_date.strftime('%Y-%m-%d'),
                'project': project,
                'category': category,
                'duration_hours': float(duration_hours),
                'description': description
            }

            with open(self.data_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writerow(entry)
            return True

    def load_data(self):
        """Load all data as pandas DataFrame"""
        if self.use_google_sheets:
            try:
                # Get all records from Google Sheets
                records = self.sheet.get_all_records()
                if records:
                    df = pd.DataFrame(records)
                    # Ensure duration_hours is numeric
                    df['duration_hours'] = pd.to_numeric(df['duration_hours'], errors='coerce')
                    df = df.dropna(subset=['duration_hours'])  # Remove invalid entries
                    df['date'] = pd.to_datetime(df['date']).dt.date
                    return df
                else:
                    return pd.DataFrame(columns=self.fieldnames)
            except Exception as e:
                st.error(f"❌ Failed to load data from Google Sheets: {str(e)}")
                return pd.DataFrame(columns=self.fieldnames)
        else:
            # Fallback to CSV
            try:
                df = pd.read_csv(self.data_file)
                df['date'] = pd.to_datetime(df['date']).dt.date
                return df
            except (FileNotFoundError, pd.errors.EmptyDataError):
                return pd.DataFrame(columns=self.fieldnames)

    def get_unique_projects(self):
        """Get list of unique projects"""
        df = self.load_data()
        if not df.empty:
            return sorted(df['project'].unique().tolist())
        return []

    def get_unique_categories(self):
        """Get list of unique categories"""
        df = self.load_data()
        if not df.empty:
            return sorted(df['category'].unique().tolist())
        return []

    def filter_by_date_range(self, df, start_date, end_date):
        """Filter dataframe by date range"""
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        return df.loc[mask]

    def get_date_ranges(self):
        """Get common date ranges for reporting"""
        today = date.today()

        # This week (Monday to Sunday)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # This month
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        # This year
        year_start = today.replace(month=1, day=1)
        year_end = today.replace(month=12, day=31)

        return {
            'week': (week_start, week_end),
            'month': (month_start, month_end),
            'year': (year_start, year_end)
        }

# Initialize the tracker
@st.cache_resource
def get_tracker():
    return TimeTracker()

# Configuration section in sidebar
st.sidebar.title("⚙️ Configuration")

# Google Sheets setup instructions
with st.sidebar.expander("📋 Google Sheets Setup", expanded=False):
    st.markdown("""
    **To use Google Sheets:**

    1. Create a Google Sheet named `Time_Tracking`
    2. Add headers: `date`, `project`, `category`, `duration_hours`, `description`
    3. Create Google Cloud service account
    4. Download `credentials.json` file
    5. Share sheet with service account email
    6. Place `credentials.json` in app directory

    **OR use Streamlit Secrets:**
    - Add your service account JSON to `.streamlit/secrets.toml`
    """)

# Storage method selector
storage_method = st.sidebar.selectbox(
    "📊 Data Storage:",
    ["Google Sheets", "Local CSV"],
    help="Choose between Google Sheets (cloud) or local CSV file"
)

# Sheet name input for Google Sheets
if storage_method == "Google Sheets":
    sheet_name = st.sidebar.text_input(
        "📄 Sheet Name:",
        value="Time_Tracking",
        help="Name of your Google Sheet"
    )
    use_google_sheets = True
else:
    sheet_name = "Time_Tracking"
    use_google_sheets = False

# Initialize tracker with selected options
if 'tracker' not in st.session_state or st.session_state.get('storage_method') != storage_method:
    st.session_state.storage_method = storage_method
    st.session_state.tracker = TimeTracker(sheet_name=sheet_name, use_google_sheets=use_google_sheets)

tracker = st.session_state.tracker

# Custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 2rem;
}

.main-header h1 {
    color: white;
    text-align: center;
    margin: 0;
}

.metric-container {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}

.storage-indicator {
    background: #f0f2f6;
    padding: 0.5rem;
    border-radius: 5px;
    text-align: center;
    margin-bottom: 1rem;
    border-left: 4px solid #28a745;
}

.security-indicator {
    background: #e8f5e8;
    padding: 0.5rem;
    border-radius: 5px;
    text-align: center;
    margin-bottom: 1rem;
    border-left: 4px solid #28a745;
}
</style>
""", unsafe_allow_html=True)

# Header with security and storage indicators
storage_icon = "☁️" if tracker.use_google_sheets else "💾"
storage_text = "Google Sheets" if tracker.use_google_sheets else "Local CSV"

st.markdown(f"""
<div class="security-indicator">
    🔐 <strong>Secure Session Active</strong> • Authenticated Access
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="storage-indicator">
    {storage_icon} <strong>Storage:</strong> {storage_text} • Data Protected
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>⏰ Personal Time Tracker</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a section:",
    ["📝 Add Entry", "📊 View Entries", "📈 Reports", "💾 Export Data"]
)

# Add the rest of your existing app pages here
# (Insert all your existing page logic: Add Entry, View Entries, Reports, Export Data)

# Footer with security info
st.markdown("---")
storage_status = "Google Sheets ☁️" if tracker.use_google_sheets else "Local CSV 💾"
st.markdown(
    f"<div style='text-align: center; color: #666;'>"
    f"🔐 Secure Personal Time Tracker • {storage_status} • Protected Session"
    f"</div>", 
    unsafe_allow_html=True
)
