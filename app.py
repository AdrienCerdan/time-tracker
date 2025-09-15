import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, date
import plotly.express as px
import hashlib
import time

# Page configuration
st.set_page_config(
    page_title="Time Tracker",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication System
def authenticate():
    """Simple password authentication using Streamlit secrets"""

    # Check if already authenticated and not timed out (2 hours)
    if (st.session_state.get("authenticated", False) and 
        time.time() - st.session_state.get("auth_time", 0) < 7200):
        return True

    # Show login form
    st.markdown("## 🔐 Time Tracker Login")
    st.markdown("Enter your password to access your personal time tracker.")

    with st.form("login_form"):
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", type="primary")

        if submit and password:
            # Get hash from secrets
            if "app_password_hash" in st.secrets:
                correct_hash = st.secrets["app_password_hash"]
                entered_hash = hashlib.sha256(password.encode()).hexdigest()

                if entered_hash == correct_hash:
                    st.session_state["authenticated"] = True
                    st.session_state["auth_time"] = time.time()
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
            else:
                st.error("❌ No password configured in secrets")
                
    return False

# Google Sheets Manager
class GoogleSheetsTracker:
    def __init__(self, sheet_name="Time_Tracking"):
        self.sheet_name = sheet_name
        self.fieldnames = ['date', 'project', 'category', 'duration_hours', 'description']
        self.connect_to_sheets()

    def connect_to_sheets(self):
        """Connect to Google Sheets using credentials from secrets"""
        try:
            if "gcp_service_account" not in st.secrets:
                st.error("❌ Google Sheets credentials not found in secrets")
                st.stop()

            # Create credentials from secrets
            credentials_info = dict(st.secrets["gcp_service_account"])
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
            client = gspread.authorize(credentials)

            # Open the sheet
            try:
                self.sheet = client.open(self.sheet_name).sheet1
            except gspread.SpreadsheetNotFound:
                st.error(f"❌ Spreadsheet '{self.sheet_name}' not found")
                st.error("Make sure the sheet exists and is shared with your service account:")
                st.code(credentials_info.get('client_email', 'email_not_found'))
                st.stop()

            # Ensure headers exist
            self.setup_headers()
            st.success("✅ Connected to Google Sheets")

        except Exception as e:
            st.error(f"❌ Failed to connect to Google Sheets: {str(e)}")
            st.stop()

    def setup_headers(self):
        """Ensure the sheet has the correct headers"""
        try:
            existing_headers = self.sheet.row_values(1)
            if not existing_headers or existing_headers != self.fieldnames:
                self.sheet.clear()
                self.sheet.append_row(self.fieldnames)
        except Exception as e:
            st.warning(f"⚠️ Could not setup headers: {e}")

    def add_entry(self, project, category, duration, description="", entry_date=None):
        """Add a new time entry"""
        if entry_date is None:
            entry_date = date.today()

        try:
            row = [
                entry_date.strftime('%Y-%m-%d'),
                project,
                category,
                f"{float(duration):.2f}".replace(",", "."),
                description
            ]
            self.sheet.append_row(row, value_input_option="USER_ENTERED")
            return True
        except Exception as e:
            st.error(f"❌ Failed to add entry: {e}")
            return False

    def load_data(self):
        """Load all data from the sheet"""
        try:
            records = self.sheet.get_all_records()
            if not records:
                return pd.DataFrame(columns=self.fieldnames)

            df = pd.DataFrame(records)
            df['duration_hours'] = pd.to_numeric(df['duration_hours'], errors='coerce')
            df = df.dropna(subset=['duration_hours'])
            df['date'] = pd.to_datetime(df['date']).dt.date
            return df
        except Exception as e:
            st.error(f"❌ Failed to load data: {e}")
            return pd.DataFrame(columns=self.fieldnames)

    def get_unique_values(self, column):
        """Get unique values for a column"""
        df = self.load_data()
        if df.empty:
            return []
        return sorted(df[column].unique().tolist())

# Initialize tracker
@st.cache_resource
def get_tracker():
    return GoogleSheetsTracker()

# Main application
def main():
    # Authentication required
    if not authenticate():
        st.stop()

    # Show logout button
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 Session")
        auth_time = st.session_state.get("auth_time", time.time())
        minutes_logged = int((time.time() - auth_time) / 60)
        st.info(f"Logged in for {minutes_logged} minutes")

        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # App header
    st.markdown("# ⏰ Personal Time Tracker")
    st.markdown("Track your time across projects and categories with Google Sheets backend.")

    # Initialize tracker
    tracker = get_tracker()

    # Navigation
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.selectbox("Choose section:", 
        ["📝 Add Entry", "📊 View Entries", "📈 Reports", "💾 Export"])

    # Add Entry Page
    if page == "📝 Add Entry":
        st.header("Add Time Entry")

        # Show existing projects/categories
        existing_projects = tracker.get_unique_values('project')
        existing_categories = tracker.get_unique_values('category')

        col1, col2 = st.columns(2)
        if existing_projects:
            col1.info(f"**Projects**: {', '.join(existing_projects[:5])}")
        if existing_categories:
            col2.info(f"**Categories**: {', '.join(existing_categories[:5])}")

        # Entry form
        with st.form("entry_form"):
            col1, col2 = st.columns(2)

            with col1:
                project = st.text_input("Project Name *", placeholder="e.g., Website, App Development")
                duration = st.number_input("Hours *", min_value=0.0, max_value=24.0, 
                                         step=0.25, format="%.2f")

            with col2:
                category = st.text_input("Category *", placeholder="e.g., coding, meeting, research")
                entry_date = st.date_input("Date", value=date.today(), max_value=date.today())

            description = st.text_area("Description (optional)", 
                                     placeholder="What did you work on?")

            if st.form_submit_button("Add Entry", type="primary"):
                if project and category and duration > 0:
                    if tracker.add_entry(project.strip(), category.strip(), 
                                       duration, description.strip(), entry_date):
                        st.success(f"✅ Added {duration}h on {project} ({category})")
                        st.rerun()
                else:
                    st.error("❌ Please fill in all required fields")

    # View Entries Page
    elif page == "📊 View Entries":
        st.header("View Time Entries")

        df = tracker.load_data()
        if df.empty:
            st.info("No entries yet. Add some time entries to get started!")
            return

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            projects = ["All"] + tracker.get_unique_values('project')
            project_filter = st.selectbox("Project", projects)

        with col2:
            categories = ["All"] + tracker.get_unique_values('category')  
            category_filter = st.selectbox("Category", categories)

        with col3:
            period_filter = st.selectbox("Period", 
                ["All", "Last 7 days", "Last 30 days", "This month"])

        # Apply filters
        filtered_df = df.copy()

        if project_filter != "All":
            filtered_df = filtered_df[filtered_df['project'] == project_filter]

        if category_filter != "All":
            filtered_df = filtered_df[filtered_df['category'] == category_filter]

        if period_filter != "All":
            today = date.today()
            if period_filter == "Last 7 days":
                cutoff = today - timedelta(days=7)
                filtered_df = filtered_df[filtered_df['date'] >= cutoff]
            elif period_filter == "Last 30 days":
                cutoff = today - timedelta(days=30)
                filtered_df = filtered_df[filtered_df['date'] >= cutoff]
            elif period_filter == "This month":
                filtered_df = filtered_df[filtered_df['date'].apply(
                    lambda x: x.month == today.month and x.year == today.year)]

        # Summary metrics
        if not filtered_df.empty:
            total_hours = filtered_df['duration_hours'].sum()
            avg_hours = filtered_df['duration_hours'].mean()

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Hours", f"{total_hours:.1f}h")
            col2.metric("Entries", len(filtered_df))
            col3.metric("Avg per Entry", f"{avg_hours:.1f}h")

            # Display data
            st.subheader("Entries")
            display_df = filtered_df.sort_values('date', ascending=False)
            display_df = display_df.copy()
            display_df['date'] = display_df['date'].astype(str)

            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No entries match your filters.")

    # Reports Page
    elif page == "📈 Reports":
        st.header("Time Reports")

        df = tracker.load_data()
        if df.empty:
            st.info("No data available for reports. Add some entries first!")
            return

        # Time period selector
        period = st.selectbox("Report Period", 
            ["Last 7 days", "Last 30 days", "This month", "All time"])

        # Filter data by period
        today = date.today()
        if period == "Last 7 days":
            filtered_df = df[df['date'] >= today - timedelta(days=7)]
        elif period == "Last 30 days":
            filtered_df = df[df['date'] >= today - timedelta(days=30)]
        elif period == "This month":
            filtered_df = df[df['date'].apply(
                lambda x: x.month == today.month and x.year == today.year)]
        else:
            filtered_df = df

        if filtered_df.empty:
            st.warning("No data for selected period.")
            return

        # Summary
        total_hours = filtered_df['duration_hours'].sum()
        st.metric("Total Hours", f"{total_hours:.1f}h")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Time by Project")
            project_hours = filtered_df.groupby('project')['duration_hours'].sum()
            if not project_hours.empty:
                fig = px.pie(values=project_hours.values, names=project_hours.index,
                           title="Hours by Project")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Time by Category") 
            category_hours = filtered_df.groupby('category')['duration_hours'].sum()
            if not category_hours.empty:
                fig = px.bar(x=category_hours.index, y=category_hours.values,
                           title="Hours by Category")
                fig.update_layout(xaxis_title="Category", yaxis_title="Hours")
                st.plotly_chart(fig, use_container_width=True)

    # Export Page
    elif page == "💾 Export":
        st.header("Export Data")

        df = tracker.load_data()
        if df.empty:
            st.info("No data to export.")
            return

        # Data preview
        st.subheader("Data Preview")
        preview_df = df.copy()
        preview_df['date'] = preview_df['date'].astype(str)
        st.dataframe(preview_df.head(), use_container_width=True)

        st.metric("Total Entries", len(df))

        # Export button
        csv_data = preview_df.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"time_tracker_export_{timestamp}.csv",
            mime="text/csv",
            type="primary"
        )

if __name__ == "__main__":
    main()
