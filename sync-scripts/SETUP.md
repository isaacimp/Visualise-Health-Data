# Health Connect Sync Setup Guide

This guide will help you set up the Python script to automatically download your Health Connect database from Google Drive.

## Prerequisites

- Python 3.7 or higher
- A Google account with the Health Connect database in Google Drive
- Health Connect app configured to auto-export to Google Drive

## Step 1: Install Python Dependencies

```bash
cd sync-scripts
python3 -m pip install -r requirements.txt
```

## Step 2: Get Google Drive API Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create a New Project**
   - Click "Select a project" at the top
   - Click "New Project"
   - Name it something like "Health Connect Sync"
   - Click "Create"

3. **Enable Google Drive API**
   - In your new project, go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click on it and click "Enable"

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen:
     - User Type: External (unless you have a Google Workspace)
     - App name: "Health Connect Sync"
     - User support email: Your email
     - Developer contact: Your email
     - Click "Save and Continue"
     - Scopes: Skip this (click "Save and Continue")
     - Test users: Add your own email address
     - Click "Save and Continue"
   - Back to creating credentials:
     - Application type: "Desktop app"
     - Name: "Health Connect Sync Desktop"
     - Click "Create"

5. **Download Credentials**
   - Click the download button (⬇) next to your newly created OAuth 2.0 Client ID
   - Save the file as `credentials.json` in the `sync-scripts` folder
   - The path should be: `/Users/isaac/Documents/tauri-charts-d3js/charted-health/sync-scripts/credentials.json`

## Step 3: Configure the Script

1. **Find your Health Connect zip filename**
   - Open Google Drive in your browser
   - Look for the Health Connect zip file (usually named something like `healthconnect.zip` or similar)
   - Note the exact filename

2. **Update the script**
   - Open `download_health_data.py`
   - Find the line: `HEALTH_CONNECT_ZIP_NAME = 'healthconnect.zip'`
   - Change it to match your actual zip filename
   - If the database file inside the zip has a different name, also update `DB_FILE_IN_ZIP`

## Step 4: First Run

```bash
cd sync-scripts
python3 download_health_data.py
```

**What happens:**
1. A browser window will open asking you to sign in to Google
2. Sign in with your Google account
3. You'll see a warning "Google hasn't verified this app" - click "Advanced" then "Go to [your app name] (unsafe)"
4. Grant permission to access Google Drive (read-only)
5. The script will download your Health Connect database
6. It will extract the data and save it as JSON

**After the first run:**
- The script saves a `token.json` file so you don't need to authenticate again
- Future runs will be automatic (no browser required)

## Step 5: Review the Output

After running, check:
- `downloaded_data/healthconnect.zip` - The downloaded zip file
- `downloaded_data/healthconnect.db` - The extracted SQLite database
- `downloaded_data/health_data_YYYYMMDD.json` - Extracted data in JSON format

Open the JSON file to see what data was extracted. You'll need this to understand:
- What tables exist in the Health Connect database
- What columns/fields are available
- How to map this data to your app's database

## Step 6: Customize Data Extraction

Once you see the database schema:

1. Open the downloaded `healthconnect.db` with a SQLite browser (like DB Browser for SQLite)
2. Explore the tables and understand the schema
3. Update the `extract_recent_health_data()` function in `download_health_data.py`
4. Write SQL queries to extract exactly the data you need

## Step 7: Set Up Daily Automation

### On macOS/Linux (cron):

1. Make the script executable:
```bash
chmod +x download_health_data.py
```

2. Edit your crontab:
```bash
crontab -e
```

3. Add a line to run daily at 2 AM:
```
0 2 * * * /usr/bin/python3 /Users/isaac/Documents/tauri-charts-d3js/charted-health/sync-scripts/download_health_data.py >> /Users/isaac/Documents/tauri-charts-d3js/charted-health/sync-scripts/sync.log 2>&1
```

### On Windows (Task Scheduler):

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Health Connect Sync"
4. Trigger: Daily at 2:00 AM
5. Action: Start a program
   - Program: `python` or `python3`
   - Arguments: `C:\path\to\download_health_data.py`
   - Start in: `C:\path\to\sync-scripts`

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the `sync-scripts` folder
- Check the filename is exactly `credentials.json`

### "Health Connect ZIP file not found"
- Check the filename in your Google Drive
- Update `HEALTH_CONNECT_ZIP_NAME` in the script to match exactly
- The script will list available files in your Google Drive to help you find it

### "ModuleNotFoundError"
- Run `pip install -r requirements.txt` again
- Make sure you're using the same Python version that has the packages installed

### Authentication issues
- Delete `token.json` and run the script again to re-authenticate
- Make sure you granted all permissions during OAuth flow

## Next Steps

After you have the data extracting correctly:
1. Examine the JSON output to understand the data structure
2. Design your app's database schema (or update existing)
3. Create an import script to load the JSON data into your app's database
4. Set up the daily automation

## Security Notes

- `credentials.json` and `token.json` contain sensitive information
- These files are gitignored by default
- Never commit these files to version control
- The script only requests read-only access to Google Drive
