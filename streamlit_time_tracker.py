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

# Set page configuration
st.set_page_config(
    page_title="Time Tracker",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

.stSelectbox > div > div > select {
    background-color: #ffffff;
}

.success-message {
    background-color: #d4edda;
    color: #155724;
    padding: 0.75rem;
    border-radius: 0.375rem;
    border: 1px solid #c3e6cb;
    margin: 1rem 0;
}

.info-box {
    background-color: #e7f3ff;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #2196F3;
    margin: 1rem 0;
}

.storage-indicator {
    background: #f0f2f6;
    padding: 0.5rem;
    border-radius: 5px;
    text-align: center;
    margin-bottom: 1rem;
    border-left: 4px solid #667eea;
}
</style>
""", unsafe_allow_html=True)

# Header with storage indicator
storage_icon = "☁️" if tracker.use_google_sheets else "💾"
storage_text = "Google Sheets" if tracker.use_google_sheets else "Local CSV"

st.markdown(f"""
<div class="storage-indicator">
    {storage_icon} <strong>Storage:</strong> {storage_text}
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>⏰ Time Tracker</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a section:",
    ["📝 Add Entry", "📊 View Entries", "📈 Reports", "💾 Export Data"]
)

# Page: Add Entry
if page == "📝 Add Entry":
    st.header("Add Time Entry")

    # Show existing projects and categories for reference
    existing_projects = tracker.get_unique_projects()
    existing_categories = tracker.get_unique_categories()

    col1, col2 = st.columns(2)

    if existing_projects:
        col1.info(f"**Existing Projects:** {', '.join(existing_projects)}")

    if existing_categories:
        col2.info(f"**Existing Categories:** {', '.join(existing_categories)}")

    # Entry form
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

    # Load data
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

            # Display table
            st.subheader("Entries")

            # Sort by date (newest first)
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

# Page: Reports
elif page == "📈 Reports":
    st.header("Time Tracking Reports")

    # Load data
    df = tracker.load_data()

    if df.empty:
        st.info("No data available for reporting. Add some time entries first!")
    else:
        # Report period selector
        report_period = st.selectbox(
            "Select Report Period:",
            ["This Week", "This Month", "This Year", "Custom Range"]
        )

        # Get date range
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

        # Filter data
        filtered_df = tracker.filter_by_date_range(df, start_date, end_date)

        if filtered_df.empty:
            st.warning(f"No data found for the selected period ({start_date} to {end_date})")
        else:
            # Summary statistics
            st.subheader("📊 Summary")
            total_hours = filtered_df['duration_hours'].sum()
            total_days = (end_date - start_date).days + 1
            avg_per_day = total_hours / total_days if total_days > 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Period", f"{start_date} to {end_date}")
            col2.metric("Total Hours", f"{total_hours:.2f}h")
            col3.metric("Total Entries", len(filtered_df))
            col4.metric("Avg Hours/Day", f"{avg_per_day:.2f}h")

            # Project breakdown
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

            # Category breakdown
            st.subheader("📋 Time by Category")
            category_totals = filtered_df.groupby('category')['duration_hours'].sum().sort_values(ascending=False)

            col1, col2 = st.columns([2, 1])

            with col1:
                if len(category_totals) > 0:
                    fig_bar = px.bar(
                        x=category_totals.index,
                        y=category_totals.values,
                        title="Time by Category",
                        labels={'x': 'Category', 'y': 'Hours'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                category_data = []
                for category, hours in category_totals.items():
                    percentage = (hours / total_hours) * 100 if total_hours > 0 else 0
                    category_data.append({
                        'Category': category,
                        'Hours': f"{hours:.2f}h", 
                        'Percentage': f"{percentage:.1f}%"
                    })

                st.dataframe(
                    pd.DataFrame(category_data),
                    hide_index=True,
                    use_container_width=True
                )

            # Project-Category breakdown
            st.subheader("🔍 Detailed Breakdown")
            project_category = filtered_df.groupby(['project', 'category'])['duration_hours'].sum().reset_index()

            if not project_category.empty:
                fig_stacked = px.bar(
                    project_category,
                    x='project',
                    y='duration_hours', 
                    color='category',
                    title="Time by Project and Category",
                    labels={'duration_hours': 'Hours', 'project': 'Project'}
                )
                st.plotly_chart(fig_stacked, use_container_width=True)

            # Daily timeline for the period
            st.subheader("📅 Daily Timeline")
            daily_totals = filtered_df.groupby('date')['duration_hours'].sum().reset_index()
            daily_totals['date_str'] = daily_totals['date'].astype(str)

            if not daily_totals.empty:
                fig_line = px.line(
                    daily_totals,
                    x='date_str',
                    y='duration_hours',
                    title="Daily Hours Logged",
                    labels={'date_str': 'Date', 'duration_hours': 'Hours'}
                )
                fig_line.update_xaxes(tickangle=45)
                st.plotly_chart(fig_line, use_container_width=True)

# Page: Export Data
elif page == "💾 Export Data":
    st.header("Export Data")

    df = tracker.load_data()

    if df.empty:
        st.info("No data available to export.")
    else:
        st.subheader("📄 Export Options")

        # Show data preview
        st.subheader("Data Preview")
        preview_df = df.copy()
        preview_df['date'] = preview_df['date'].astype(str)
        st.dataframe(preview_df.head(10), use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Entries", len(df))

        with col2:
            st.metric("Total Hours", f"{df['duration_hours'].sum():.2f}h")

        # Export buttons
        st.subheader("📥 Download Data")

        # Prepare CSV data
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

        # Export filtered data
        st.subheader("📋 Export Filtered Data")

        col1, col2 = st.columns(2)

        with col1:
            export_project = st.selectbox(
                "Project Filter:",
                ["All"] + sorted(df['project'].unique().tolist())
            )

        with col2:
            export_period = st.selectbox(
                "Period Filter:",
                ["All", "This Week", "This Month", "This Year"]
            )

        # Apply export filters
        export_df = df.copy()

        if export_project != "All":
            export_df = export_df[export_df['project'] == export_project]

        if export_period != "All":
            date_ranges = tracker.get_date_ranges()
            period_map = {"This Week": "week", "This Month": "month", "This Year": "year"}
            start_date, end_date = date_ranges[period_map[export_period]]
            export_df = tracker.filter_by_date_range(export_df, start_date, end_date)

        if not export_df.empty:
            export_csv_data = export_df.copy()
            export_csv_data['date'] = export_csv_data['date'].astype(str)
            export_csv_string = export_csv_data.to_csv(index=False)

            st.download_button(
                label=f"Download Filtered Data as CSV ({len(export_df)} entries)",
                data=export_csv_string,
                file_name=f"time_tracking_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data matches the selected filters.")

# Footer
st.markdown("---")
storage_status = "Google Sheets ☁️" if tracker.use_google_sheets else "Local CSV 💾"
st.markdown(
    f"<div style='text-align: center; color: #666;'>"
    f"⏰ Time Tracker - {storage_status} - Built with Streamlit"
    f"</div>", 
    unsafe_allow_html=True
)
