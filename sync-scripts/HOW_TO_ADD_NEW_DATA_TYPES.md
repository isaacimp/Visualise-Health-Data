# How to Add New Health Data Types

This guide shows you how to add new health metrics from Health Connect to your app.

## Overview

The process has 3 main steps:
1. **Explore** the Health Connect database to find the data
2. **Extract** the data in `extract_health_data.py`
3. **Import** the data in `import_to_app_db.py`

## Step 1: Explore Available Data

First, see what tables are available in Health Connect:

```bash
cd sync-scripts/downloaded_data
sqlite3 health_connect_export.db ".tables"
```

This shows all available health data types. For example:
- `weight_record_table` - Body weight
- `distance_record_table` - Distance traveled
- `exercise_session_record_table` - Exercise sessions
- `nutrition_record_table` - Nutrition data
- `hydration_record_table` - Water intake
- etc.

### Examine the Schema

To see what fields a table has:

```bash
sqlite3 health_connect_export.db "PRAGMA table_info(weight_record_table);"
```

### Look at Sample Data

To see actual data:

```bash
sqlite3 health_connect_export.db "SELECT * FROM weight_record_table LIMIT 5;"
```

## Step 2: Add Extraction Function

### Example: Adding Weight Tracking

Open `extract_health_data.py` and add a new function:

```python
def extract_weight(db_path, days_back=30):
    """
    Extract body weight data.

    Fields in weight_record_table:
    - weight: Weight in kilograms (INTEGER - multiply by 1000)
    - start_time: Timestamp when measured
    """
    print(f"Extracting weight data (last {days_back} days)...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate cutoff timestamp
    cutoff_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

    # Query the data
    query = """
        SELECT
            row_id,
            start_time,
            end_time,
            local_date,
            weight  -- This is in grams (weight * 1000)
        FROM weight_record_table
        WHERE start_time >= ?
        ORDER BY start_time DESC
    """

    cursor.execute(query, (cutoff_ms,))
    rows = cursor.fetchall()

    # Transform the data
    weight_data = []
    for row in rows:
        weight_kg = row['weight'] / 1000.0  # Convert grams to kg

        weight_data.append({
            'id': row['row_id'],
            'timestamp': row['start_time'],
            'datetime': datetime.fromtimestamp(row['start_time'] / 1000).isoformat(),
            'date': str(row['local_date']),
            'weight_kg': round(weight_kg, 2),
            'weight_lbs': round(weight_kg * 2.20462, 1)  # Also provide pounds
        })

    conn.close()
    print(f"  Found {len(weight_data)} weight records")
    return weight_data
```

### Add to main() Function

In the `main()` function of `extract_health_data.py`, add:

```python
# After the other extractions
weight = extract_weight(db_path, days_back)

# Add to the health_data dict
health_data = {
    'extracted_at': datetime.now().isoformat(),
    'days_back': days_back,
    'data': {
        'steps': steps,
        'sleep': sleep,
        'heart_rate': heart_rate,
        'weight': weight  # Add this line
    },
    'summary': {
        'steps_records': len(steps),
        'sleep_sessions': len(sleep),
        'heart_rate_records': len(heart_rate),
        'weight_records': len(weight)  # Add this line
    }
}
```

## Step 3: Add Import Function

Open `import_to_app_db.py` and add an import function:

```python
def import_weight_data(cursor, weight_data, dry_run=False):
    """Import body weight data."""
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
            description="Body weight from Health Connect",
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
```

### Add to main() Function

In the `main()` function of `import_to_app_db.py`, add calls to your new function:

```python
# In dry run section
weight_imported, weight_skipped = import_weight_data(
    cursor, health_data['data']['weight'], dry_run=True
)

# In the actual import section
import_weight_data(cursor, health_data['data']['weight'], dry_run=False)

# In the summary
print(f"  Weight: {weight_imported} would be imported, {weight_skipped} would be skipped")
```

## Common Patterns

### Instant Measurements (Weight, Blood Pressure, etc.)
- Use `start_time` as the timestamp
- No `duration_seconds`
- Usually just one or two values

### Range/Session Data (Sleep, Exercise, etc.)
- Has both `start_time` and `end_time`
- Calculate `duration_seconds` = `(end_time - start_time) / 1000`
- May have related tables (like sleep stages)

### Series Data (Heart Rate, Steps, etc.)
- May have a parent table and a series/samples table
- Parent table has the record, series table has individual measurements
- Join them using `parent_key` = `row_id`

### Related Tables

Some data types have multiple related tables. Example: Sleep

```python
# Main session
cursor.execute("SELECT * FROM sleep_session_record_table WHERE ...")
sessions = cursor.fetchall()

# For each session, get related data
for session in sessions:
    cursor.execute(
        "SELECT * FROM sleep_stages_table WHERE parent_key = ?",
        (session['row_id'],)
    )
    stages = cursor.fetchall()
```

## Health Connect Field Types

Common field conversions:

- **Weight**: Stored in grams, divide by 1000 for kg
- **Distance**: Stored in meters
- **Energy**: Stored in calories
- **Time**: Unix timestamps in milliseconds
- **Dates**: Format YYYYMMDD as INTEGER

## Testing

1. **Run extraction** to see the data:
   ```bash
   python3 extract_health_data.py
   cat extracted_data/health_data_*.json | python3 -m json.tool | less
   ```

2. **Dry run import** to preview:
   ```bash
   python3 import_to_app_db.py
   # Answer 'no' when asked to proceed
   ```

3. **Actually import**:
   ```bash
   python3 import_to_app_db.py
   # Answer 'yes' when asked to proceed
   ```

## Tips

1. **Start simple**: Extract just the basic fields first, add complexity later
2. **Check units**: Health Connect often uses metric units (kg, meters, etc.)
3. **Handle nulls**: Some fields may be null/missing
4. **Timestamps**: Always in milliseconds, convert to seconds for Python datetime
5. **Test with LIMIT**: Use `LIMIT 5` when exploring to avoid huge outputs

## Example: Quick Reference

```bash
# 1. Explore the table
sqlite3 downloaded_data/health_connect_export.db "PRAGMA table_info(YOUR_TABLE_NAME);"
sqlite3 downloaded_data/health_connect_export.db "SELECT * FROM YOUR_TABLE_NAME LIMIT 3;"

# 2. Add extraction function to extract_health_data.py
# 3. Add import function to import_to_app_db.py
# 4. Test it
python3 extract_health_data.py
python3 import_to_app_db.py
```

That's it! You can now add any health data type from Health Connect to your app.
