#!/usr/bin/env python3
"""
Import Health Connect data into the app's SQLite database.

This script shows you how to:
1. Read the extracted JSON data
2. Transform it to match your app's schema
3. Insert it into your app's database

The app uses a flexible tracker/entries system, so we'll create
trackers for each health metric and import the data as entries.

Usage:
  python3 import_to_app_db.py              # Interactive mode (asks for confirmation)
  python3 import_to_app_db.py --auto       # Automatic mode (no confirmation)
  python3 import_to_app_db.py --dry-run    # Dry run only (no changes)
"""

import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path


def create_or_update_tracker(cursor, tracker_id, name, icon, description, color, fields):
    """Create or update a tracker in the database."""
    # Check if tracker exists
    cursor.execute("SELECT id FROM trackers WHERE id = ?", (tracker_id,))
    exists = cursor.fetchone()

    if exists:
        # Update existing tracker
        cursor.execute("""
            UPDATE trackers
            SET name = ?, icon = ?, description = ?, color = ?, fields = ?, modified_at = ?
            WHERE id = ?
        """, (name, icon, description, color, json.dumps(fields), datetime.now().isoformat(), tracker_id))
        print(f"  Updated tracker: {name}")
    else:
        # Create new tracker
        cursor.execute("""
            INSERT INTO trackers (id, name, icon, description, color, fields, created_at, modified_at, use_count, last_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)
        """, (tracker_id, name, icon, description, color, json.dumps(fields),
              datetime.now().isoformat(), datetime.now().isoformat()))
        print(f"  Created tracker: {name}")


def import_steps_data(cursor, steps_data, dry_run=False):
    """
    Import steps data into the app database.

    Each step record becomes an entry with the step count.
    """
    print(f"\nImporting {len(steps_data)} step records...")

    # Define the Steps tracker
    tracker_id = "health-connect-steps"
    fields = [
        {
            "id": "steps",
            "name": "Steps",
            "type": "number",
            "required": True,
            "min": 0
        }
    ]

    if not dry_run:
        create_or_update_tracker(
            cursor,
            tracker_id=tracker_id,
            name="Steps",
            icon="👟",
            description="Daily step count from Health Connect",
            color="#4CAF50",
            fields=fields
        )

    # Import entries
    imported = 0
    skipped = 0

    for record in steps_data:
        entry_id = f"hc-steps-{record['id']}"

        # Check if entry already exists
        if not dry_run:
            cursor.execute("SELECT id FROM entries WHERE id = ?", (entry_id,))
            if cursor.fetchone():
                skipped += 1
                continue

        # Create entry data
        entry_data = {
            "steps": record['steps']
        }

        # Use the start time as the timestamp
        timestamp = record['start_datetime']

        if not dry_run:
            cursor.execute("""
                INSERT INTO entries (
                    id, tracker_id, tracker_name, timestamp,
                    fields_snapshot, data, tags, notes, duration_seconds,
                    created_at, modified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                tracker_id,
                "Steps",
                timestamp,
                json.dumps(fields),
                json.dumps(entry_data),
                None,  # tags
                None,  # notes
                (record['end_time'] - record['start_time']) / 1000,  # duration in seconds
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        imported += 1

    print(f"  Imported: {imported}, Skipped (already exists): {skipped}")
    return imported, skipped


def import_sleep_data(cursor, sleep_data, dry_run=False):
    """
    Import sleep session data.

    Each sleep session becomes an entry with duration and stage breakdown.
    """
    print(f"\nImporting {len(sleep_data)} sleep sessions...")

    # Define the Sleep tracker
    tracker_id = "health-connect-sleep"
    fields = [
        {
            "id": "duration_hours",
            "name": "Duration (hours)",
            "type": "number",
            "required": True
        },
        {
            "id": "light_sleep_minutes",
            "name": "Light Sleep (min)",
            "type": "number"
        },
        {
            "id": "deep_sleep_minutes",
            "name": "Deep Sleep (min)",
            "type": "number"
        },
        {
            "id": "rem_sleep_minutes",
            "name": "REM Sleep (min)",
            "type": "number"
        },
        {
            "id": "awake_minutes",
            "name": "Awake (min)",
            "type": "number"
        }
    ]

    if not dry_run:
        create_or_update_tracker(
            cursor,
            tracker_id=tracker_id,
            name="Sleep",
            icon="😴",
            description="Sleep sessions from Health Connect",
            color="#9C27B0",
            fields=fields
        )

    # Import entries
    imported = 0
    skipped = 0

    for record in sleep_data:
        entry_id = f"hc-sleep-{record['id']}"

        if not dry_run:
            cursor.execute("SELECT id FROM entries WHERE id = ?", (entry_id,))
            if cursor.fetchone():
                skipped += 1
                continue

        # Extract stage summary
        stage_summary = record['stage_summary']

        entry_data = {
            "duration_hours": record['duration_hours'],
            "light_sleep_minutes": stage_summary.get('light', {}).get('total_minutes', 0),
            "deep_sleep_minutes": stage_summary.get('deep', {}).get('total_minutes', 0),
            "rem_sleep_minutes": stage_summary.get('rem', {}).get('total_minutes', 0),
            "awake_minutes": stage_summary.get('awake', {}).get('total_minutes', 0)
        }

        # Add notes if available
        notes = record.get('notes') or record.get('title')

        timestamp = record['start_datetime']

        if not dry_run:
            cursor.execute("""
                INSERT INTO entries (
                    id, tracker_id, tracker_name, timestamp,
                    fields_snapshot, data, tags, notes, duration_seconds,
                    created_at, modified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                tracker_id,
                "Sleep",
                timestamp,
                json.dumps(fields),
                json.dumps(entry_data),
                None,
                notes,
                record['duration_minutes'] * 60,  # duration in seconds
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        imported += 1

    print(f"  Imported: {imported}, Skipped (already exists): {skipped}")
    return imported, skipped


def import_heart_rate_data(cursor, heart_rate_data, dry_run=False):
    """
    Import heart rate data.

    Each heart rate record becomes an entry with average/min/max BPM.
    """
    print(f"\nImporting {len(heart_rate_data)} heart rate records...")

    # Define the Heart Rate tracker
    tracker_id = "health-connect-heart-rate"
    fields = [
        {
            "id": "avg_bpm",
            "name": "Average BPM",
            "type": "number",
            "required": True,
            "min": 30,
            "max": 220
        },
        {
            "id": "min_bpm",
            "name": "Min BPM",
            "type": "number"
        },
        {
            "id": "max_bpm",
            "name": "Max BPM",
            "type": "number"
        },
        {
            "id": "measurement_count",
            "name": "Measurements",
            "type": "number"
        }
    ]

    if not dry_run:
        create_or_update_tracker(
            cursor,
            tracker_id=tracker_id,
            name="Heart Rate",
            icon="❤️",
            description="Heart rate measurements from Health Connect",
            color="#F44336",
            fields=fields
        )

    # Import entries
    imported = 0
    skipped = 0

    for record in heart_rate_data:
        # Skip records with no measurements
        if not record['statistics']['avg_bpm']:
            skipped += 1
            continue

        entry_id = f"hc-heart-rate-{record['id']}"

        if not dry_run:
            cursor.execute("SELECT id FROM entries WHERE id = ?", (entry_id,))
            if cursor.fetchone():
                skipped += 1
                continue

        stats = record['statistics']
        entry_data = {
            "avg_bpm": stats['avg_bpm'],
            "min_bpm": stats['min_bpm'],
            "max_bpm": stats['max_bpm'],
            "measurement_count": stats['count']
        }

        timestamp = record['start_datetime']

        if not dry_run:
            cursor.execute("""
                INSERT INTO entries (
                    id, tracker_id, tracker_name, timestamp,
                    fields_snapshot, data, tags, notes, duration_seconds,
                    created_at, modified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                tracker_id,
                "Heart Rate",
                timestamp,
                json.dumps(fields),
                json.dumps(entry_data),
                None,
                None,
                (record['end_time'] - record['start_time']) / 1000,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        imported += 1

    print(f"  Imported: {imported}, Skipped (already exists): {skipped}")
    return imported, skipped


def import_weight_data(cursor, weight_data, dry_run=False):
    """Import body weight data from Renpho."""
    print(f"\nImporting {len(weight_data)} weight records...")

    # Define the Weight tracker
    tracker_id = "health-connect-weight"
    fields = [
        {
            "id": "weight_kg",
            "name": "Weight (kg)",
            "type": "number",
            "required": True,
            "min": 0
        },
        {
            "id": "weight_lbs",
            "name": "Weight (lbs)",
            "type": "number",
            "required": False
        }
    ]

    if not dry_run:
        create_or_update_tracker(
            cursor,
            tracker_id=tracker_id,
            name="Weight",
            icon="⚖️",
            description="Body weight from Renpho scale",
            color="#FF9800",
            fields=fields
        )

    # Import entries
    imported = 0
    skipped = 0

    for record in weight_data:
        entry_id = f"hc-weight-{record['id']}"

        if not dry_run:
            cursor.execute("SELECT id FROM entries WHERE id = ?", (entry_id,))
            if cursor.fetchone():
                skipped += 1
                continue

        entry_data = {
            "weight_kg": record['weight_kg'],
            "weight_lbs": record['weight_lbs']
        }

        timestamp = record['datetime']

        if not dry_run:
            cursor.execute("""
                INSERT INTO entries (
                    id, tracker_id, tracker_name, timestamp,
                    fields_snapshot, data, tags, notes, duration_seconds,
                    created_at, modified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                tracker_id,
                "Weight",
                timestamp,
                json.dumps(fields),
                json.dumps(entry_data),
                None,
                None,
                None,  # No duration for instant measurements
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        imported += 1

    print(f"  Imported: {imported}, Skipped: {skipped}")
    return imported, skipped


def import_nutrition_data(cursor, nutrition_data, dry_run=False):
    """
    Import nutrition data from Cronometer.

    Each nutrition record (meal/food) becomes an entry with calories and macros.
    """
    print(f"\nImporting {len(nutrition_data)} nutrition records...")

    # Define the Nutrition tracker
    tracker_id = "health-connect-nutrition"
    fields = [
        {
            "id": "meal_name",
            "name": "Meal/Food Name",
            "type": "text",
            "required": True
        },
        {
            "id": "meal_type",
            "name": "Meal Type",
            "type": "text",
            "required": False
        },
        {
            "id": "calories",
            "name": "Calories",
            "type": "number",
            "required": True,
            "min": 0
        },
        {
            "id": "protein_g",
            "name": "Protein (g)",
            "type": "number"
        },
        {
            "id": "carbs_g",
            "name": "Carbs (g)",
            "type": "number"
        },
        {
            "id": "fat_g",
            "name": "Fat (g)",
            "type": "number"
        },
        {
            "id": "fiber_g",
            "name": "Fiber (g)",
            "type": "number"
        },
        {
            "id": "sugar_g",
            "name": "Sugar (g)",
            "type": "number"
        }
    ]

    if not dry_run:
        create_or_update_tracker(
            cursor,
            tracker_id=tracker_id,
            name="Nutrition",
            icon="🍽️",
            description="Nutrition tracking from Cronometer",
            color="#4CAF50",
            fields=fields
        )

    # Import entries
    imported = 0
    skipped = 0

    for record in nutrition_data:
        entry_id = f"hc-nutrition-{record['id']}"

        if not dry_run:
            cursor.execute("SELECT id FROM entries WHERE id = ?", (entry_id,))
            if cursor.fetchone():
                skipped += 1
                continue

        # Build entry data
        entry_data = {
            "meal_name": record['meal_name'],
            "meal_type": record['meal_type'],
            "calories": record['calories'],
            "protein_g": record['macros']['protein_g'],
            "carbs_g": record['macros']['carbs_g'],
            "fat_g": record['macros']['fat_g'],
            "fiber_g": record['macros']['fiber_g'],
            "sugar_g": record['macros']['sugar_g'],
            # Store all detailed data in JSON for future use
            "fats": record['fats'],
            "micros": record['micros']
        }

        timestamp = record['start_datetime']

        if not dry_run:
            cursor.execute("""
                INSERT INTO entries (
                    id, tracker_id, tracker_name, timestamp,
                    fields_snapshot, data, tags, notes, duration_seconds,
                    created_at, modified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                tracker_id,
                "Nutrition",
                timestamp,
                json.dumps(fields),
                json.dumps(entry_data),
                None,
                None,
                None,  # No duration
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        imported += 1

    print(f"  Imported: {imported}, Skipped: {skipped}")
    return imported, skipped


def main():
    """Main import function."""
    # Parse command line arguments
    auto_mode = '--auto' in sys.argv
    dry_run_only = '--dry-run' in sys.argv

    script_dir = Path(__file__).parent
    extracted_dir = script_dir / 'extracted_data'

    # Find the most recent extracted data file
    json_files = sorted(extracted_dir.glob('health_data_*.json'), reverse=True)

    if not json_files:
        print("Error: No extracted data files found.")
        print(f"Please run extract_health_data.py first")
        return 1

    json_file = json_files[0]

    print("=" * 60)
    print("Import Health Connect Data to App Database")
    print("=" * 60)
    print(f"\nData file: {json_file.name}")

    # Load the extracted data
    with open(json_file, 'r') as f:
        health_data = json.load(f)

    print(f"Extracted at: {health_data['extracted_at']}")
    print(f"Summary: {health_data['summary']}")

    # Ask for confirmation
    print("\n" + "=" * 60)
    print("This will import the data into your app's database.")
    print("Existing entries will NOT be duplicated (checked by ID).")
    print("=" * 60)

    # Dry run first to show what would be imported
    print("\nDry run (no changes will be made)...")

    # Connect to app database
    app_db_path = script_dir.parent / 'data.sqlite'

    if not app_db_path.exists():
        print(f"\nWarning: App database not found at {app_db_path}")
        print("Creating new database...")

    conn = sqlite3.connect(app_db_path)
    cursor = conn.cursor()

    # Import data (dry run)
    steps_imported, steps_skipped = import_steps_data(cursor, health_data['data']['steps'], dry_run=True)
    sleep_imported, sleep_skipped = import_sleep_data(cursor, health_data['data']['sleep'], dry_run=True)
    hr_imported, hr_skipped = import_heart_rate_data(cursor, health_data['data']['heart_rate'], dry_run=True)
    weight_imported, weight_skipped = import_weight_data(cursor, health_data['data']['weight'], dry_run=True)

    # Import nutrition data if available (may not be in older extracted data files)
    if 'nutrition' in health_data['data']:
        nutrition_imported, nutrition_skipped = import_nutrition_data(cursor, health_data['data']['nutrition'], dry_run=True)
    else:
        nutrition_imported, nutrition_skipped = 0, 0
        print("\nNote: No nutrition data found in extracted file. Run extract_health_data.py again to include nutrition data.")

    print("\n" + "=" * 60)
    print("Dry run complete. Summary:")
    print(f"  Steps: {steps_imported} would be imported, {steps_skipped} would be skipped")
    print(f"  Sleep: {sleep_imported} would be imported, {sleep_skipped} would be skipped")
    print(f"  Heart Rate: {hr_imported} would be imported, {hr_skipped} would be skipped")
    print(f"  Weight: {weight_imported} would be imported, {weight_skipped} would be skipped")
    print(f"  Nutrition: {nutrition_imported} would be imported, {nutrition_skipped} would be skipped")
    print("=" * 60)

    # If dry-run only, exit here
    if dry_run_only:
        print("\nDry run only - no changes made.")
        conn.close()
        return 0

    # Ask for confirmation (unless auto mode)
    if not auto_mode:
        try:
            response = input("\nProceed with import? (yes/no): ").strip().lower()
        except EOFError:
            print("\nNo input received. Use --auto flag for non-interactive mode.")
            conn.close()
            return 1

        if response != 'yes':
            print("Import cancelled.")
            conn.close()
            return 0
    else:
        print("\nAuto mode - proceeding with import...")

    # Actual import
    print("\nImporting data...")
    import_steps_data(cursor, health_data['data']['steps'], dry_run=False)
    import_sleep_data(cursor, health_data['data']['sleep'], dry_run=False)
    import_heart_rate_data(cursor, health_data['data']['heart_rate'], dry_run=False)
    import_weight_data(cursor, health_data['data']['weight'], dry_run=False)
    if 'nutrition' in health_data['data']:
        import_nutrition_data(cursor, health_data['data']['nutrition'], dry_run=False)

    # Commit changes
    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("✓ Import complete!")
    print("=" * 60)
    print("\nYour app database now contains Health Connect data.")
    print("You can now view it in your app's charts!")

    return 0


if __name__ == '__main__':
    exit(main())
