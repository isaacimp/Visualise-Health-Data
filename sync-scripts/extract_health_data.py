#!/usr/bin/env python3
"""
Extract specific health data types from Health Connect database.

This script shows how to extract:
- Steps
- Sleep sessions and stages
- Heart rate

You can use this as a template to add more data types.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path


def extract_steps(db_path, days_back=30):
    """
    Extract step count data.

    Schema:
    - start_time, end_time: Unix timestamps in milliseconds
    - count: Number of steps
    - local_date: Date in YYYYMMDD format
    """
    print(f"Extracting steps data (last {days_back} days)...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate cutoff timestamp (milliseconds)
    cutoff_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

    query = """
        SELECT
            row_id,
            start_time,
            end_time,
            local_date,
            count as steps,
            app_info_id
        FROM steps_record_table
        WHERE start_time >= ?
          AND app_info_id = 10  -- Only Garmin Connect data
        ORDER BY start_time DESC
    """

    cursor.execute(query, (cutoff_ms,))
    rows = cursor.fetchall()

    # Convert to list of dicts with human-readable timestamps
    steps_data = []
    for row in rows:
        steps_data.append({
            'id': row['row_id'],
            'start_time': row['start_time'],
            'end_time': row['end_time'],
            'start_datetime': datetime.fromtimestamp(row['start_time'] / 1000).isoformat(),
            'end_datetime': datetime.fromtimestamp(row['end_time'] / 1000).isoformat(),
            'date': str(row['local_date']),
            'steps': row['steps']
        })

    conn.close()
    print(f"  Found {len(steps_data)} step records")
    return steps_data


def extract_sleep(db_path, days_back=30):
    """
    Extract sleep session data with sleep stages.

    Sleep stages:
    - 1: Awake (during sleep)
    - 2: Sleeping (unspecified)
    - 3: Out of bed
    - 4: Light sleep
    - 5: Deep sleep
    - 6: REM sleep
    """
    print(f"Extracting sleep data (last {days_back} days)...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate cutoff timestamp
    cutoff_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

    # Get sleep sessions
    session_query = """
        SELECT
            row_id,
            start_time,
            end_time,
            local_date,
            title,
            notes
        FROM sleep_session_record_table
        WHERE start_time >= ?
        ORDER BY start_time DESC
    """

    cursor.execute(session_query, (cutoff_ms,))
    sessions = cursor.fetchall()

    sleep_data = []
    for session in sessions:
        session_id = session['row_id']

        # Get sleep stages for this session
        stages_query = """
            SELECT
                stage_start_time,
                stage_end_time,
                stage_type
            FROM sleep_stages_table
            WHERE parent_key = ?
            ORDER BY stage_start_time
        """

        cursor.execute(stages_query, (session_id,))
        stages = cursor.fetchall()

        # Convert stages to readable format
        stage_names = {
            1: 'awake',
            2: 'sleeping',
            3: 'out_of_bed',
            4: 'light',
            5: 'deep',
            6: 'rem'
        }

        stages_list = []
        for stage in stages:
            stages_list.append({
                'start_time': stage['stage_start_time'],
                'end_time': stage['stage_end_time'],
                'start_datetime': datetime.fromtimestamp(stage['stage_start_time'] / 1000).isoformat(),
                'end_datetime': datetime.fromtimestamp(stage['stage_end_time'] / 1000).isoformat(),
                'stage': stage_names.get(stage['stage_type'], 'unknown'),
                'stage_type': stage['stage_type'],
                'duration_minutes': (stage['stage_end_time'] - stage['stage_start_time']) / 1000 / 60
            })

        # Calculate sleep statistics
        total_duration = (session['end_time'] - session['start_time']) / 1000 / 60  # minutes

        sleep_data.append({
            'id': session_id,
            'start_time': session['start_time'],
            'end_time': session['end_time'],
            'start_datetime': datetime.fromtimestamp(session['start_time'] / 1000).isoformat(),
            'end_datetime': datetime.fromtimestamp(session['end_time'] / 1000).isoformat(),
            'date': str(session['local_date']) if session['local_date'] else None,
            'duration_minutes': total_duration,
            'duration_hours': round(total_duration / 60, 2),
            'title': session['title'],
            'notes': session['notes'],
            'stages': stages_list,
            'stage_summary': calculate_stage_summary(stages_list)
        })

    conn.close()
    print(f"  Found {len(sleep_data)} sleep sessions")
    return sleep_data


def calculate_stage_summary(stages):
    """Calculate summary statistics for sleep stages."""
    summary = {}

    for stage in stages:
        stage_name = stage['stage']
        duration = stage['duration_minutes']

        if stage_name not in summary:
            summary[stage_name] = {
                'total_minutes': 0,
                'count': 0
            }

        summary[stage_name]['total_minutes'] += duration
        summary[stage_name]['count'] += 1

    # Round the totals
    for stage_name in summary:
        summary[stage_name]['total_minutes'] = round(summary[stage_name]['total_minutes'], 1)
        summary[stage_name]['total_hours'] = round(summary[stage_name]['total_minutes'] / 60, 2)

    return summary


def extract_heart_rate(db_path, days_back=30):
    """
    Extract heart rate data.

    Heart rate is stored in two tables:
    - heart_rate_record_table: The main record
    - heart_rate_record_series_table: Individual BPM measurements
    """
    print(f"Extracting heart rate data (last {days_back} days)...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate cutoff timestamp
    cutoff_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

    # Get heart rate records
    record_query = """
        SELECT
            row_id,
            start_time,
            end_time,
            local_date
        FROM heart_rate_record_table
        WHERE start_time >= ?
        ORDER BY start_time DESC
    """

    cursor.execute(record_query, (cutoff_ms,))
    records = cursor.fetchall()

    heart_rate_data = []
    for record in records:
        record_id = record['row_id']

        # Get individual heart rate measurements
        series_query = """
            SELECT
                beats_per_minute,
                epoch_millis
            FROM heart_rate_record_series_table
            WHERE parent_key = ?
            ORDER BY epoch_millis
        """

        cursor.execute(series_query, (record_id,))
        measurements = cursor.fetchall()

        # Convert measurements to readable format
        measurements_list = []
        bpm_values = []

        for measurement in measurements:
            bpm = measurement['beats_per_minute']
            bpm_values.append(bpm)

            measurements_list.append({
                'bpm': bpm,
                'timestamp': measurement['epoch_millis'],
                'datetime': datetime.fromtimestamp(measurement['epoch_millis'] / 1000).isoformat()
            })

        # Calculate statistics
        if bpm_values:
            avg_bpm = sum(bpm_values) / len(bpm_values)
            min_bpm = min(bpm_values)
            max_bpm = max(bpm_values)
        else:
            avg_bpm = min_bpm = max_bpm = None

        heart_rate_data.append({
            'id': record_id,
            'start_time': record['start_time'],
            'end_time': record['end_time'],
            'start_datetime': datetime.fromtimestamp(record['start_time'] / 1000).isoformat(),
            'end_datetime': datetime.fromtimestamp(record['end_time'] / 1000).isoformat(),
            'date': str(record['local_date']) if record['local_date'] else None,
            'measurements': measurements_list,
            'statistics': {
                'count': len(measurements_list),
                'avg_bpm': round(avg_bpm, 1) if avg_bpm else None,
                'min_bpm': min_bpm,
                'max_bpm': max_bpm
            }
        })

    conn.close()
    print(f"  Found {len(heart_rate_data)} heart rate records")
    return heart_rate_data


def extract_weight(db_path, days_back=90):
    """
    Extract body weight data from Renpho.

    Weight is stored in grams, converted to kg and lbs.
    """
    print(f"Extracting weight data (last {days_back} days)...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate cutoff timestamp
    cutoff_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

    query = """
        SELECT
            row_id,
            time,
            local_date,
            weight
        FROM weight_record_table
        WHERE time >= ?
          AND app_info_id = 6  -- Only Renpho data
        ORDER BY time DESC
    """

    cursor.execute(query, (cutoff_ms,))
    rows = cursor.fetchall()

    weight_data = []
    for row in rows:
        weight_grams = row['weight']
        weight_kg = weight_grams / 1000.0
        weight_lbs = weight_kg * 2.20462

        weight_data.append({
            'id': row['row_id'],
            'timestamp': row['time'],
            'datetime': datetime.fromtimestamp(row['time'] / 1000).isoformat(),
            'date': str(row['local_date']) if row['local_date'] else None,
            'weight_kg': round(weight_kg, 2),
            'weight_lbs': round(weight_lbs, 1)
        })

    conn.close()
    print(f"  Found {len(weight_data)} weight records")
    return weight_data


def extract_nutrition(db_path, days_back=90):
    """
    Extract nutrition data from Cronometer.

    Energy is stored in calories (kcal).
    Macros are in grams.
    Micronutrients are in grams (need conversion to mg/mcg).

    Meal types:
    - 0: Unknown/Unspecified
    - 1: Breakfast
    - 2: Lunch
    - 3: Dinner
    - 4: Snack
    """
    print(f"Extracting nutrition data (last {days_back} days)...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Calculate cutoff timestamp
    cutoff_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

    query = """
        SELECT
            row_id,
            start_time,
            end_time,
            local_date,
            meal_type,
            meal_name,
            energy,
            protein,
            total_carbohydrate,
            total_fat,
            saturated_fat,
            trans_fat,
            unsaturated_fat,
            polyunsaturated_fat,
            monounsaturated_fat,
            dietary_fiber,
            sugar,
            sodium,
            cholesterol,
            calcium,
            iron,
            potassium,
            vitamin_a,
            vitamin_c,
            vitamin_d,
            vitamin_e,
            vitamin_k,
            vitamin_b6,
            vitamin_b12,
            thiamin,
            riboflavin,
            niacin,
            folate,
            magnesium,
            phosphorus,
            zinc
        FROM nutrition_record_table
        WHERE start_time >= ?
          AND app_info_id = 2  -- Only Cronometer data
        ORDER BY start_time DESC
    """

    cursor.execute(query, (cutoff_ms,))
    rows = cursor.fetchall()

    meal_type_names = {
        0: 'unspecified',
        1: 'breakfast',
        2: 'lunch',
        3: 'dinner',
        4: 'snack'
    }

    nutrition_data = []
    for row in rows:
        # Energy is in calories
        calories = row['energy'] / 1000.0 if row['energy'] else 0

        nutrition_data.append({
            'id': row['row_id'],
            'start_time': row['start_time'],
            'end_time': row['end_time'],
            'start_datetime': datetime.fromtimestamp(row['start_time'] / 1000).isoformat(),
            'end_datetime': datetime.fromtimestamp(row['end_time'] / 1000).isoformat(),
            'date': str(row['local_date']) if row['local_date'] else None,
            'meal_type': meal_type_names.get(row['meal_type'], 'unspecified'),
            'meal_type_code': row['meal_type'],
            'meal_name': row['meal_name'] or 'Unknown',
            'calories': round(calories, 1),
            'macros': {
                'protein_g': round(row['protein'], 1) if row['protein'] else 0,
                'carbs_g': round(row['total_carbohydrate'], 1) if row['total_carbohydrate'] else 0,
                'fat_g': round(row['total_fat'], 1) if row['total_fat'] else 0,
                'fiber_g': round(row['dietary_fiber'], 1) if row['dietary_fiber'] else 0,
                'sugar_g': round(row['sugar'], 1) if row['sugar'] else 0,
            },
            'fats': {
                'saturated_g': round(row['saturated_fat'], 1) if row['saturated_fat'] else 0,
                'trans_g': round(row['trans_fat'], 1) if row['trans_fat'] else 0,
                'polyunsaturated_g': round(row['polyunsaturated_fat'], 1) if row['polyunsaturated_fat'] else 0,
                'monounsaturated_g': round(row['monounsaturated_fat'], 1) if row['monounsaturated_fat'] else 0,
            },
            'micros': {
                'sodium_mg': round(row['sodium'] * 1000, 1) if row['sodium'] else 0,
                'cholesterol_mg': round(row['cholesterol'] * 1000, 1) if row['cholesterol'] else 0,
                'calcium_mg': round(row['calcium'] * 1000, 1) if row['calcium'] else 0,
                'iron_mg': round(row['iron'] * 1000, 1) if row['iron'] else 0,
                'potassium_mg': round(row['potassium'] * 1000, 1) if row['potassium'] else 0,
                'magnesium_mg': round(row['magnesium'] * 1000, 1) if row['magnesium'] else 0,
                'phosphorus_mg': round(row['phosphorus'] * 1000, 1) if row['phosphorus'] else 0,
                'zinc_mg': round(row['zinc'] * 1000, 1) if row['zinc'] else 0,
                'vitamin_a_mcg': round(row['vitamin_a'] * 1000000, 1) if row['vitamin_a'] else 0,
                'vitamin_c_mg': round(row['vitamin_c'] * 1000, 1) if row['vitamin_c'] else 0,
                'vitamin_d_mcg': round(row['vitamin_d'] * 1000000, 1) if row['vitamin_d'] else 0,
                'vitamin_e_mg': round(row['vitamin_e'] * 1000, 1) if row['vitamin_e'] else 0,
                'vitamin_k_mcg': round(row['vitamin_k'] * 1000000, 1) if row['vitamin_k'] else 0,
                'vitamin_b6_mg': round(row['vitamin_b6'] * 1000, 1) if row['vitamin_b6'] else 0,
                'vitamin_b12_mcg': round(row['vitamin_b12'] * 1000000, 1) if row['vitamin_b12'] else 0,
                'thiamin_mg': round(row['thiamin'] * 1000, 1) if row['thiamin'] else 0,
                'riboflavin_mg': round(row['riboflavin'] * 1000, 1) if row['riboflavin'] else 0,
                'niacin_mg': round(row['niacin'] * 1000, 1) if row['niacin'] else 0,
                'folate_mcg': round(row['folate'] * 1000000, 1) if row['folate'] else 0,
            }
        })

    conn.close()
    print(f"  Found {len(nutrition_data)} nutrition records")
    return nutrition_data


def main():
    """Extract health data and save to JSON."""
    script_dir = Path(__file__).parent
    db_path = script_dir / 'downloaded_data' / 'health_connect_export.db'
    output_dir = script_dir / 'extracted_data'

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run download_health_data.py first")
        return 1

    print("=" * 60)
    print("Health Connect Data Extraction")
    print("=" * 60)
    print()

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Extract data
    days_back = 30  # Adjust this to get more/less history

    steps = extract_steps(db_path, days_back)
    sleep = extract_sleep(db_path, days_back)
    heart_rate = extract_heart_rate(db_path, days_back)
    weight = extract_weight(db_path, 90)  # Get more weight history
    nutrition = extract_nutrition(db_path, 90)  # Get nutrition history

    # Combine all data
    health_data = {
        'extracted_at': datetime.now().isoformat(),
        'days_back': days_back,
        'data': {
            'steps': steps,
            'sleep': sleep,
            'heart_rate': heart_rate,
            'weight': weight,
            'nutrition': nutrition
        },
        'summary': {
            'steps_records': len(steps),
            'sleep_sessions': len(sleep),
            'heart_rate_records': len(heart_rate),
            'weight_records': len(weight),
            'nutrition_records': len(nutrition)
        }
    }

    # Save to JSON
    output_file = output_dir / f'health_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(health_data, f, indent=2)

    print()
    print("=" * 60)
    print(f"✓ Data extracted successfully!")
    print(f"✓ Output: {output_file}")
    print()
    print("Summary:")
    print(f"  Steps records: {len(steps)}")
    print(f"  Sleep sessions: {len(sleep)}")
    print(f"  Heart rate records: {len(heart_rate)}")
    print(f"  Weight records: {len(weight)}")
    print(f"  Nutrition records: {len(nutrition)}")
    print()
    print("Next steps:")
    print("1. Review the JSON file to see the data structure")
    print("2. Run import_to_app_db.py to import this data into your app")

    return 0


if __name__ == '__main__':
    exit(main())
