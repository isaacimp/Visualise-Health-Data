#!/usr/bin/env python3
"""
Health Connect Google Drive Sync Script

This script downloads the Health Connect SQLite database from Google Drive
and extracts health data into JSON format for easy import into your app.

Setup:
1. pip install -r requirements.txt
2. Follow instructions in SETUP.md to get Google Drive API credentials
3. Run this script daily (manually or via cron/Task Scheduler)
"""

import os
import sqlite3
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / 'downloaded_data'
CREDENTIALS_FILE = SCRIPT_DIR / 'credentials.json'
TOKEN_FILE = SCRIPT_DIR / 'token.json'
OUTPUT_FILE = DATA_DIR / f'health_data_{datetime.now().strftime("%Y%m%d")}.json'

# Health Connect ZIP file name in Google Drive (adjust this to match your file)
HEALTH_CONNECT_ZIP_NAME = 'Health Connect.zip'  # Change this to your actual filename
# Name of the database file inside the ZIP (usually healthconnect.db)
DB_FILE_IN_ZIP = 'health_connect_export.db'  # Adjust if different inside the zip


def authenticate_google_drive():
    """Authenticate with Google Drive API."""
    creds = None

    # Load existing token if available
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Credentials file not found at {CREDENTIALS_FILE}\n"
                    "Please follow SETUP.md to get your Google Drive API credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        TOKEN_FILE.write_text(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def find_health_connect_file(service):
    """Find the Health Connect ZIP file in Google Drive."""
    print(f"Searching for '{HEALTH_CONNECT_ZIP_NAME}' in Google Drive...")

    # Search for the file
    results = service.files().list(
        q=f"name='{HEALTH_CONNECT_ZIP_NAME}' and trashed=false",
        spaces='drive',
        fields='files(id, name, modifiedTime)',
        orderBy='modifiedTime desc'
    ).execute()

    files = results.get('files', [])

    if not files:
        print(f"\nAvailable files in your Google Drive:")
        all_files = service.files().list(
            spaces='drive',
            fields='files(id, name, modifiedTime)',
            orderBy='modifiedTime desc',
            pageSize=20
        ).execute()

        for f in all_files.get('files', []):
            print(f"  - {f['name']} (modified: {f['modifiedTime']})")

        raise FileNotFoundError(
            f"\nHealth Connect ZIP file '{HEALTH_CONNECT_ZIP_NAME}' not found in Google Drive.\n"
            "Please update HEALTH_CONNECT_ZIP_NAME in the script to match your file name."
        )

    file = files[0]
    print(f"Found: {file['name']} (last modified: {file['modifiedTime']})")
    return file


def download_file(service, file_id, destination):
    """Download a file from Google Drive."""
    print(f"Downloading to {destination}...")

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while done is False:
        status, done = downloader.next_chunk()
        if status:
            print(f"Download {int(status.progress() * 100)}%")

    # Write to file
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(fh.getvalue())
    print(f"Download complete: {destination}")


def extract_db_from_zip(zip_path, extract_to_dir):
    """Extract the database file from the downloaded zip."""
    print(f"\nExtracting database from {zip_path}...")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # List all files in the zip
        file_list = zip_ref.namelist()
        print(f"Files in zip: {', '.join(file_list)}")

        # Try to find the database file
        db_file = None
        for file in file_list:
            if file.endswith('.db') or file == DB_FILE_IN_ZIP:
                db_file = file
                break

        if not db_file:
            raise FileNotFoundError(
                f"No .db file found in the zip archive.\n"
                f"Files found: {', '.join(file_list)}\n"
                f"Please update DB_FILE_IN_ZIP in the script."
            )

        print(f"Extracting {db_file}...")
        zip_ref.extract(db_file, extract_to_dir)

        extracted_path = extract_to_dir / db_file
        print(f"Database extracted to: {extracted_path}")
        return extracted_path


def extract_health_data(db_path):
    """
    Extract health data from Health Connect SQLite database.

    Note: This is a template function. You'll need to adjust the SQL queries
    based on the actual schema of your Health Connect database.
    """
    print(f"\nExtracting data from {db_path}...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()

    # First, let's explore the database schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"Found tables: {', '.join(tables)}")

    extracted_data = {
        'extracted_at': datetime.now().isoformat(),
        'tables': {},
        'schema': {}
    }

    # Extract schema and data for each table
    for table in tables:
        print(f"  Processing table: {table}")

        # Get table schema
        cursor.execute(f"PRAGMA table_info({table});")
        schema = [dict(row) for row in cursor.fetchall()]
        extracted_data['schema'][table] = schema

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"    Rows: {count}")

        # Extract all data from the table
        # You may want to add date filters here to only get new data
        cursor.execute(f"SELECT * FROM {table};")
        rows = [dict(row) for row in cursor.fetchall()]
        extracted_data['tables'][table] = rows

    conn.close()
    return extracted_data


def extract_recent_health_data(db_path, days_back=7):
    """
    Extract recent health data (last N days).

    This is an alternative to extract_health_data that only gets recent data.
    Adjust the queries based on your actual Health Connect schema.
    """
    print(f"\nExtracting last {days_back} days of data from {db_path}...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate cutoff date
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

    extracted_data = {
        'extracted_at': datetime.now().isoformat(),
        'days_back': days_back,
        'cutoff_date': cutoff_date,
        'data': {}
    }

    # You'll need to adjust these queries based on your actual Health Connect schema
    # Common Health Connect tables might include:
    # - steps_record
    # - heart_rate_record
    # - sleep_session_record
    # - exercise_session_record
    # - weight_record
    # etc.

    # Example: Extract steps (adjust table/column names as needed)
    try:
        # This is just an example - adjust based on actual schema
        cursor.execute("""
            SELECT * FROM steps_record
            WHERE date(start_time) >= date(?)
            ORDER BY start_time DESC
        """, (cutoff_date,))
        extracted_data['data']['steps'] = [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        print("    Note: 'steps_record' table not found (adjust query to match your schema)")

    conn.close()
    return extracted_data


def main():
    """Main execution function."""
    print("=" * 60)
    print("Health Connect Data Sync")
    print("=" * 60)

    try:
        # Create data directory
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Authenticate with Google Drive
        service = authenticate_google_drive()

        # Find and download the Health Connect ZIP
        health_file = find_health_connect_file(service)
        zip_path = DATA_DIR / 'healthconnect.zip'
        download_file(service, health_file['id'], zip_path)

        # Extract database from zip
        db_path = extract_db_from_zip(zip_path, DATA_DIR)

        # Extract data
        print("\nChoose extraction method:")
        print("1. Extract ALL data (may be large)")
        print("2. Extract recent data (last 7 days)")

        # For automation, default to recent data
        # Comment this out if you want to be prompted each time
        choice = '2'

        if choice == '1':
            data = extract_health_data(db_path)
        else:
            data = extract_recent_health_data(db_path, days_back=7)

        # Save to JSON
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"\n✓ Data extracted successfully!")
        print(f"✓ Output saved to: {OUTPUT_FILE}")
        print(f"\nNext steps:")
        print(f"1. Review the extracted data in {OUTPUT_FILE}")
        print(f"2. Adjust the extraction queries based on the actual schema")
        print(f"3. Create an import script to load this data into your app's database")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
