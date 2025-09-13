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
import csv
import os

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
        try:
            entered_password = st.session_state.get("password", "")

            # Get password hash from secrets
            if "app_password_hash" in st.secrets:
                correct_hash = st.secrets["app_password_hash"]
            else:
                # For local testing, allow a default password
                st.warning("⚠️ No password hash configured in secrets. Using default for local testing.")
                # Hash of "admin123" for local testing
                correct_hash = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"

            entered_hash = hashlib.sha256(entered_password.encode()).hexdigest()

            if entered_hash == correct_hash:
                st.session_state["authenticated"] = True
                st.session_state["auth_timestamp"] = time.time()
                # Clear password from session for security
                if "password" in st.session_state:
                    del st.session_state["password"]
                st.success("✅ Access granted! Loading your time tracker...")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state["authenticated"] = False
                st.error("❌ Incorrect password. Access denied.")

        except Exception as e:
            st.error(f"❌ Authentication error: {str(e)}")
            st.session_state["authenticated"] = False

    # Check if already authenticated and not timed out (1 hour = 3600 seconds)
    current_time = time.time()
    auth_timestamp = st.session_state.get("auth_timestamp", 0)

    if (st.session_state.get("authenticated", False) and 
        (current_time - auth_timestamp) < 3600):
        return True

    # Reset authentication state if timed out
    st.session_state["authenticated"] = False

    # Show login form
    st.markdown("## 🔐 Personal Time Tracker")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🛡️ Secure Access Required")

        st.info("""
        This is your personal time tracking application.
        Please enter your password to continue.
        """)

        # Password input field
        password = st.text_input(
            "🔑 Enter Password:", 
            type="password", 
            key="password_input",
            placeholder="Your secure password",
            help="Enter the password configured for this app"
        )

        # Login button
        if st.button("🔓 Login", type="primary", use_container_width=True):
            if password:
                # Store password in session state for the check function
                st.session_state["password"] = password
                password_entered()
            else:
                st.error("❌ Please enter a password")

        st.markdown("---")

        # Local development info
        if not ("app_password_hash" in st.secrets):
            st.warning("""
            **Local Development Mode Detected**

            No password hash found in secrets. For local testing, use password: `admin123`

            For production, add your password hash to secrets.toml:
            ```
            app_password_hash = "your-generated-hash"
            ```
            """)

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

# Check authentication ONLY if secrets indicate this should be secured
# This allows the app to work without authentication for local development
should_authenticate = False

try:
    # Check if running in a secured environment
    if "app_password_hash" in st.secrets or os.getenv("STREAMLIT_SHARING_MODE"):
        should_authenticate = True
except:
    # If secrets are not available, don't require authentication (local dev)
    should_authenticate = False

# Apply authentication if needed
if should_authenticate and not secure_personal_app():
    st.stop()

# Add logout functionality in sidebar if authenticated
if st.session_state.get("authenticated", False) or not should_authenticate:
    # Only show logout if authentication was required
    if should_authenticate:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Session Info")

            auth_time = st.session_state.get("auth_timestamp", time.time())
            session_duration = int((time.time() - auth_time) / 60)  # minutes
            timeout_remaining = max(0, 60 - session_duration)  # minutes until timeout

            st.info(f"""
            **Session Active:** {session_duration} min  
            **Auto-logout in:** {timeout_remaining} min
            """)

            if st.button("🚪 Logout", type="secondary", help="Clear session and logout"):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("👋 Logged out successfully")
                st.rerun()

class TimeTracker:
    def __init__(self, sheet_name='Time_Tracking', use_google_sheets=True):
        self.sheet_name = sheet_name
        self.use_google_sheets = use_google_sheets
        self.fieldnames = ['date', 'project', 'category', 'duration_hours', 'description']

        if self.use_google_sheets:
            self.setup_google_sheets()
        else:
            # Fallback to CSV
            self.data_file = 'time_tracking_data.csv'
            self.ensure_data_file_exists()

    def setup_google_sheets(self):
        """Setup Google Sheets connection with better error handling"""
        try:
            # Try Streamlit secrets first
            if "gcp_service_account" in st.secrets:
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

            # Try local credentials file
            elif os.path.exists('credentials.json'):
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                credentials = Credentials.from_service_account_file('credentials.json', scopes=scopes)
                self.client = gspread.authorize(credentials)
                self.sheet = self.client.open(self.sheet_name).sheet1
                self.ensure_sheet_headers()
                st.success("✅ Connected to Google Sheets successfully!")

            else:
                st.warning("⚠️ No Google Sheets credentials found. Using local CSV storage.")
                self.use_google_sheets = False
                self.data_file = 'time_tracking_data.csv'
                self.ensure_data_file_exists()

        except Exception as e:
            st.warning(f"⚠️ Could not connect to Google Sheets: {str(e)}")
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
        """Create CSV file with headers if it doesn't exist"""
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
            # CSV fallback
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
                records = self.sheet.get_all_records()
                if records:
                    df = pd.DataFrame(records)
                    df['duration_hours'] = pd.to_numeric(df['duration_hours'], errors='coerce')
                    df = df.dropna(subset=['duration_hours'])
                    df['date'] = pd.to_datetime(df['date']).dt.date
                    return df
                else:
                    return pd.DataFrame(columns=self.fieldnames)
            except Exception as e:
                st.error(f"❌ Failed to load data from Google Sheets: {str(e)}")
                return pd.DataFrame(columns=self.fieldnames)
        else:
            # CSV fallback
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

# Initialize tracker
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
</style>
""", unsafe_allow_html=True)

# Show security indicator if authenticated
if st.session_state.get("authenticated", False):
    st.markdown(f"""
    <div class="storage-indicator">
        🔐 <strong>Secure Session Active</strong> • Authenticated Access
    </div>
    """, unsafe_allow_html=True)

# Storage indicator
storage_icon = "☁️" if tracker.use_google_sheets else "💾"
storage_text = "Google Sheets" if tracker.use_google_sheets else "Local CSV"

st.markdown(f"""
<div class="storage-indicator">
    {storage_icon} <strong>Storage:</strong> {storage_text}
</div>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>⏰ Time Tracker</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a section:",
    ["📝 Add Entry", "📊 View Entries", "📈 Reports", "💾 Export Data"]
)

# Page: Add Entry
if page == "📝 Add Entry":
    st.header("Add Time Entry")

    existing_projects = tracker.get_unique_projects()
    existing_categories = tracker.get_unique_categories()

    col1, col2 = st.columns(2)

    if existing_projects:
        col1.info(f"**Existing Projects:** {', '.join(existing_projects)}")

    if existing_categories:
        col2.info(f"**Existing Categories:** {', '.join(existing_categories)}")

    with st.form("add_entry_form"):
        col1, col2 = st.columns(2)

        with col1:
            project = st.text_input(
                "Project Name *", 
                placeholder="e.g., Project_A, Website_Redesign"
            )
            duration = st.number_input(
                "Duration (hours) *", 
                min_value=0.0, 
                max_value=24.0, 
                step=0.25, 
                format="%.2f"
            )

        with col2:
            category = st.text_input(
                "Category *", 
                placeholder="e.g., coding, meeting, research"
            )
            entry_date = st.date_input(
                "Date *", 
                value=date.today(),
                max_value=date.today()
            )

        description = st.text_area(
            "Description (optional)", 
            placeholder="Brief description of the work done"
        )

        submitted = st.form_submit_button("Add Entry", type="primary")

        if submitted:
            if project and category and duration > 0:
                success = tracker.add_entry(
                    project=project.strip(),
                    category=category.strip(), 
                    duration_hours=duration,
                    description=description.strip(),
                    entry_date=entry_date
                )

                if success:
                    st.success(f"✅ Added: {duration}h on {project} ({category}) - {entry_date}")
                    st.rerun()
            else:
                st.error("❌ Please fill in all required fields (Project, Category, Duration > 0)")

# Page: View Entries
elif page == "📊 View Entries":
    st.header("View Time Entries")

    df = tracker.load_data()

    if df.empty:
        st.info("No time entries found. Add some entries to get started!")
    else:
        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            project_filter = st.selectbox(
                "Filter by Project:",
                ["All"] + sorted(df['project'].unique().tolist())
            )

        with col2:
            category_filter = st.selectbox(
                "Filter by Category:",
                ["All"] + sorted(df['category'].unique().tolist())
            )

        with col3:
            date_filter = st.selectbox(
                "Filter by Period:",
                ["All", "This Week", "This Month", "This Year", "Custom Range"]
            )

        # Apply filters
        filtered_df = df.copy()

        if project_filter != "All":
            filtered_df = filtered_df[filtered_df['project'] == project_filter]

        if category_filter != "All":
            filtered_df = filtered_df[filtered_df['category'] == category_filter]

        if date_filter != "All":
            date_ranges = tracker.get_date_ranges()
            if date_filter == "This Week":
                start_date, end_date = date_ranges['week']
                filtered_df = tracker.filter_by_date_range(filtered_df, start_date, end_date)
            elif date_filter == "This Month":
                start_date, end_date = date_ranges['month']
                filtered_df = tracker.filter_by_date_range(filtered_df, start_date, end_date)
            elif date_filter == "This Year":
                start_date, end_date = date_ranges['year']
                filtered_df = tracker.filter_by_date_range(filtered_df, start_date, end_date)
            elif date_filter == "Custom Range":
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
                with col2:
                    end_date = st.date_input("End Date", value=date.today())
                filtered_df = tracker.filter_by_date_range(filtered_df, start_date, end_date)

        # Display summary
        if not filtered_df.empty:
            total_hours = filtered_df['duration_hours'].sum()
            total_entries = len(filtered_df)
            avg_hours = filtered_df['duration_hours'].mean()

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Hours", f"{total_hours:.2f}h")
            col2.metric("Total Entries", total_entries)
            col3.metric("Average Hours/Entry", f"{avg_hours:.2f}h")

            st.subheader("Entries")

            display_df = filtered_df.sort_values('date', ascending=False).copy()
            display_df['date'] = display_df['date'].astype(str)
            display_df['duration_hours'] = display_df['duration_hours'].apply(lambda x: f"{x:.2f}h")

            st.dataframe(
                display_df,
                column_config={
                    "date": "Date",
                    "project": "Project", 
                    "category": "Category",
                    "duration_hours": "Duration",
                    "description": "Description"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No entries match the selected filters.")

# Page: Reports (simplified for now)
elif page == "📈 Reports":
    st.header("Time Tracking Reports")

    df = tracker.load_data()

    if df.empty:
        st.info("No data available for reporting. Add some time entries first!")
    else:
        report_period = st.selectbox(
            "Select Report Period:",
            ["This Week", "This Month", "This Year", "Custom Range"]
        )

        date_ranges = tracker.get_date_ranges()

        if report_period == "Custom Range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", value=date.today())
        else:
            period_map = {
                "This Week": "week",
                "This Month": "month", 
                "This Year": "year"
            }
            start_date, end_date = date_ranges[period_map[report_period]]

        filtered_df = tracker.filter_by_date_range(df, start_date, end_date)

        if filtered_df.empty:
            st.warning(f"No data found for the selected period ({start_date} to {end_date})")
        else:
            st.subheader("📊 Summary")
            total_hours = filtered_df['duration_hours'].sum()
            total_days = (end_date - start_date).days + 1
            avg_per_day = total_hours / total_days if total_days > 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Period", f"{start_date} to {end_date}")
            col2.metric("Total Hours", f"{total_hours:.2f}h")
            col3.metric("Total Entries", len(filtered_df))
            col4.metric("Avg Hours/Day", f"{avg_per_day:.2f}h")

            st.subheader("🎯 Time by Project")
            project_totals = filtered_df.groupby('project')['duration_hours'].sum().sort_values(ascending=False)

            col1, col2 = st.columns([2, 1])

            with col1:
                if len(project_totals) > 0:
                    fig_pie = px.pie(
                        values=project_totals.values,
                        names=project_totals.index,
                        title="Time Distribution by Project"
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                project_data = []
                for project, hours in project_totals.items():
                    percentage = (hours / total_hours) * 100 if total_hours > 0 else 0
                    project_data.append({
                        'Project': project,
                        'Hours': f"{hours:.2f}h",
                        'Percentage': f"{percentage:.1f}%"
                    })

                st.dataframe(
                    pd.DataFrame(project_data),
                    hide_index=True,
                    use_container_width=True
                )

# Page: Export Data
elif page == "💾 Export Data":
    st.header("Export Data")

    df = tracker.load_data()

    if df.empty:
        st.info("No data available to export.")
    else:
        st.subheader("📄 Export Options")

        st.subheader("Data Preview")
        preview_df = df.copy()
        preview_df['date'] = preview_df['date'].astype(str)
        st.dataframe(preview_df.head(10), use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Entries", len(df))

        with col2:
            st.metric("Total Hours", f"{df['duration_hours'].sum():.2f}h")

        st.subheader("📥 Download Data")

        csv_data = df.copy()
        csv_data['date'] = csv_data['date'].astype(str)
        csv_string = csv_data.to_csv(index=False)

        st.download_button(
            label="Download All Data as CSV",
            data=csv_string,
            file_name=f"time_tracking_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary"
        )

# Footer
st.markdown("---")
storage_status = "Google Sheets ☁️" if tracker.use_google_sheets else "Local CSV 💾"
auth_status = "🔐 Secure" if st.session_state.get("authenticated", False) else "🔓 Open"
st.markdown(
    f"<div style='text-align: center; color: #666;'>"
    f"⏰ Time Tracker • {storage_status} • {auth_status} • Built with Streamlit"
    f"</div>", 
    unsafe_allow_html=True
)
