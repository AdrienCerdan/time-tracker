# Personal Time Tracker

A clean, secure time tracking application built with Streamlit and Google Sheets.

## ✨ Features

- 🔐 **Secure Access**: Password-protected personal time tracker
- ☁️ **Google Sheets Backend**: All data stored in your personal Google Sheet
- 📊 **Visual Reports**: Interactive charts and analytics
- 📱 **Responsive Design**: Works on desktop and mobile
- 💾 **Easy Export**: Download your data as CSV anytime

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Google Sheets
1. Create a Google Sheet named "Time_Tracking"
2. Set up a Google Cloud service account ([guide here](https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account))
3. Share your sheet with the service account email
4. Download the credentials JSON

### 3. Setup Authentication
```bash
# Use the password utility to set your password
python password_utility.py
```

### 4. Configure Secrets

**For Local Development** - Create `.streamlit/secrets.toml`:
```toml
# Your password hash (generate with password_utility.py)
app_password_hash = "your-password-hash-here"

# Your Google Cloud service account credentials
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id" 
private_key = """-----BEGIN PRIVATE KEY-----
your-private-key-here
-----END PRIVATE KEY-----"""
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service%40your-project.iam.gserviceaccount.com"
```

**For Streamlit Cloud** - Add the same content to your app's secrets in the dashboard.

### 5. Run the App
```bash
streamlit run app.py
```

## 📊 Usage

### Adding Time Entries
1. Go to "Add Entry" section
2. Fill in project, category, hours, and optional description
3. Click "Add Entry"

### Viewing Data
- **View Entries**: See all your logged time with filtering options
- **Reports**: Visual analytics with charts and summaries
- **Export**: Download your data as CSV

### Data Structure
Your Google Sheet will have these columns:
- `date`: Entry date (YYYY-MM-DD)
- `project`: Project name
- `category`: Activity category (coding, meeting, research, etc.)
- `duration_hours`: Time spent in hours
- `description`: Optional description

## 🔐 Security

- **Password Protection**: Secure SHA-256 hashed authentication
- **Personal Data**: Only you can access your time tracking data
- **Google Sheets**: Data stored in your personal Google account
- **Session Timeout**: Automatic logout after 2 hours

## 🛠️ Files

- `app.py` - Main application
- `password_utility.py` - Tool to manage passwords and hashes
- `requirements.txt` - Python dependencies
- `.streamlit/secrets.toml` - Local configuration (not committed to git)
- `.streamlit/config.toml` - Streamlit settings

## 🚀 Deployment

### Streamlit Community Cloud
1. Push your code to a public GitHub repository (without secrets)
2. Connect to [share.streamlit.io](https://share.streamlit.io)
3. Deploy your app
4. Add secrets in the Streamlit Cloud dashboard
5. Your app will be available at a public URL with password protection

## 💡 Tips

- **Consistent Naming**: Use consistent project and category names for better reporting
- **Regular Logging**: Log time daily for accurate tracking
- **Backup**: Your data is automatically backed up in Google Sheets
- **Mobile**: The app works great on mobile browsers

## 🔧 Troubleshooting

### Password Issues
- Use `python password_utility.py` to test passwords and generate hashes
- Make sure the hash in secrets.toml matches your password

### Google Sheets Issues  
- Verify the sheet is named "Time_Tracking" (case-sensitive)
- Ensure the sheet is shared with your service account email
- Check that APIs are enabled in Google Cloud Console

### App Won't Start
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check that secrets.toml has valid TOML syntax
- Ensure Google Sheets credentials are correct

## 📝 License

This project is for personal use. Feel free to modify and adapt for your needs.
