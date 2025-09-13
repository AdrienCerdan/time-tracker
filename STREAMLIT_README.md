# Streamlit Time Tracker

A comprehensive web-based time tracking application built with Streamlit for local use.

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   streamlit run streamlit_time_tracker.py
   ```

3. **Open in Browser**:
   - The app will automatically open in your default browser
   - If not, go to: http://localhost:8501

## ✨ Features

### 📝 Add Entry
- **Easy Form**: Add time entries with project, category, duration, and description
- **Smart Suggestions**: Shows existing projects and categories for consistency
- **Date Selection**: Choose any date (defaults to today)
- **Validation**: Ensures all required fields are filled

### 📊 View Entries
- **Interactive Table**: Sortable and filterable data display
- **Smart Filters**: Filter by project, category, and time period
- **Summary Metrics**: Total hours, entries count, and averages
- **Custom Date Ranges**: Flexible date filtering options

### 📈 Reports & Analytics
- **Multiple Periods**: Weekly, monthly, yearly, or custom ranges
- **Visual Charts**: 
  - Pie charts for project distribution
  - Bar charts for category breakdown
  - Stacked charts for project-category analysis
  - Timeline charts for daily tracking
- **Detailed Statistics**: Hours, percentages, and trends
- **Summary Cards**: Key metrics at a glance

### 💾 Export Data
- **CSV Export**: Download all data or filtered subsets
- **Data Preview**: See your data before exporting
- **Flexible Filtering**: Export specific projects or time periods
- **Timestamped Files**: Automatic file naming with date/time

## 🗂️ Data Storage

- **File Format**: CSV format (`time_tracking_data.csv`)
- **Location**: Same directory as the application
- **Compatibility**: Works with Excel, Google Sheets, or any CSV editor
- **Backup**: Simply copy the CSV file to backup your data

## 🎨 Interface Features

- **Responsive Design**: Works on desktop and mobile browsers
- **Clean UI**: Modern, professional interface
- **Navigation**: Easy sidebar navigation between sections
- **Real-time Updates**: Changes reflected immediately
- **Custom Styling**: Professional color scheme and layout

## 📊 Sample Usage Workflow

1. **Start the app**: `streamlit run streamlit_time_tracker.py`
2. **Add entries**: Use the "Add Entry" section to log your work
3. **View data**: Check "View Entries" to see and filter your logged time
4. **Analyze**: Use "Reports" to understand your time patterns
5. **Export**: Download your data from "Export Data" section

## 🛠️ Technical Details

- **Framework**: Streamlit (Python web framework)
- **Charts**: Plotly for interactive visualizations
- **Data**: Pandas for data manipulation
- **Storage**: CSV files for data persistence
- **Local Only**: No external dependencies or cloud services

## 📋 Data Structure

The app stores data in CSV format with these columns:
- `date`: Entry date (YYYY-MM-DD)
- `project`: Project name
- `category`: Activity category
- `duration_hours`: Time in hours (decimal)
- `description`: Optional work description

## 🔧 Customization

The app is designed for local use and can be customized by:
- Modifying the CSS styling in the code
- Adding new chart types
- Extending the filtering options
- Adding new export formats

## 💡 Tips for Best Results

1. **Consistent Naming**: Use consistent project and category names
2. **Daily Logging**: Log time regularly for better insights
3. **Clear Categories**: Use descriptive categories like "coding", "meeting", "research"
4. **Backup Data**: Periodically copy your CSV file as backup
5. **Review Reports**: Use weekly/monthly reports to track productivity trends

## 🐛 Troubleshooting

- **App won't start**: Check that all requirements are installed
- **Missing data**: Ensure CSV file is in the same directory
- **Charts not loading**: Verify Plotly is properly installed
- **Port issues**: If 8501 is busy, Streamlit will suggest an alternative port
