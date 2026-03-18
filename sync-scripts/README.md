# Health Connect Sync Scripts

This folder contains scripts to sync your Health Connect data from Google Drive to your local app database.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Drive API credentials:**
   - Follow the detailed instructions in [SETUP.md](SETUP.md)

3. **Run the sync script:**
   ```bash
   python download_health_data.py
   ```

## Files

- `download_health_data.py` - Main script that downloads and extracts Health Connect data
- `requirements.txt` - Python dependencies
- `SETUP.md` - Detailed setup instructions
- `credentials.json` - Google Drive API credentials (you need to create this)
- `token.json` - OAuth token (created automatically on first run)
- `downloaded_data/` - Downloaded databases and extracted JSON files

## How It Works

1. Authenticates with Google Drive API
2. Downloads the latest Health Connect SQLite database
3. Extracts health data from the database
4. Saves it as JSON for easy import into your app

## Customization

After your first run, you'll need to customize the data extraction:

1. Open the downloaded SQLite database to see its schema
2. Edit the SQL queries in `download_health_data.py` to match your needs
3. Map the extracted data to your app's database schema

## Next Steps

Once you have data extracting correctly, you can:
- Create an import script to load the JSON into your app's database
- Set up daily automation (cron on Mac/Linux, Task Scheduler on Windows)
- Integrate this with your Tauri app

See [SETUP.md](SETUP.md) for detailed instructions.
