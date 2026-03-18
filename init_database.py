#!/usr/bin/env python3
"""
Initialize the app database with the required schema.

Run this once to create the database tables.
"""

import sqlite3
from pathlib import Path

def init_database():
    """Create the database schema."""
    db_path = Path(__file__).parent / 'data.sqlite'

    print(f"Initializing database at {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create trackers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trackers (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL UNIQUE,
            icon VARCHAR,
            description TEXT,
            color VARCHAR,
            fields JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            use_count INTEGER DEFAULT 0,
            last_used TIMESTAMP
        )
    """)

    # Create entries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id VARCHAR PRIMARY KEY,
            tracker_id VARCHAR NOT NULL,
            tracker_name VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            fields_snapshot JSON NOT NULL,
            data JSON NOT NULL,
            tags TEXT,
            notes TEXT,
            duration_seconds INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create presets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presets (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            tracker_id VARCHAR NOT NULL,
            icon VARCHAR,
            prefilled_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entries_timestamp
        ON entries(timestamp DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entries_tracker
        ON entries(tracker_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entries_tracker_name
        ON entries(tracker_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_trackers_name
        ON trackers(name)
    """)

    conn.commit()
    conn.close()

    print("✓ Database initialized successfully!")
    print(f"✓ Tables created: trackers, entries, presets")
    print(f"✓ Indexes created")
    print("\nNext step: Run the import script to load your Health Connect data:")
    print("  cd sync-scripts && python3 import_to_app_db.py --auto")

if __name__ == '__main__':
    init_database()
