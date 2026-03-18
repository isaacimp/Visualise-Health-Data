# Complete Health Connect Sync Guide

## 🎯 What We Built

A complete system to automatically sync your Health Connect data from Google Drive to your app:

1. **Download Script** (`download_health_data.py`) - Downloads the Health Connect database from Google Drive
2. **Extraction Script** (`extract_health_data.py`) - Extracts steps, sleep, and heart rate data into JSON
3. **Import Script** (`import_to_app_db.py`) - Imports the data into your app's database
4. **Guide for Adding More** (`HOW_TO_ADD_NEW_DATA_TYPES.md`) - Template for adding new health metrics

## 📁 Files Created

```
sync-scripts/
├── download_health_data.py       # Downloads from Google Drive
├── extract_health_data.py        # Extracts health metrics
├── import_to_app_db.py           # Imports to your app
├── requirements.txt              # Python dependencies
├── SETUP.md                      # Initial setup instructions
├── README.md                     # Quick start guide
├── HOW_TO_ADD_NEW_DATA_TYPES.md # Tutorial for adding new metrics
├── COMPLETE_GUIDE.md             # This file
├── credentials.json              # (You create) Google Drive API credentials
├── token.json                    # (Auto-created) OAuth token
├── downloaded_data/              # Downloaded and extracted databases
└── extracted_data/               # JSON files with extracted health data
```

## 🚀 Quick Start (Daily Usage)

Once everything is set up, your daily workflow is simple:

### Option 1: Three Commands (Manual)

```bash
cd sync-scripts

# 1. Download latest data from Google Drive
python3 download_health_data.py

# 2. Extract the metrics you want
python3 extract_health_data.py

# 3. Import to your app (it will ask for confirmation)
python3 import_to_app_db.py
```

### Option 2: Automated (Future)

Set up a cron job or Task Scheduler to run these automatically daily.

## 📊 Current Data Types

### 1. Steps
- **What it tracks**: Step count per time period
- **Fields**: Step count
- **Example**: 156 steps from 2:15 PM to 2:16 PM

### 2. Sleep
- **What it tracks**: Sleep sessions with stage breakdown
- **Fields**:
  - Total duration (hours)
  - Light sleep (minutes)
  - Deep sleep (minutes)
  - REM sleep (minutes)
  - Awake time (minutes)
- **Example**: 7.5 hours sleep with 5 hours light, 0.9 hours deep, 1.5 hours REM

### 3. Heart Rate
- **What it tracks**: Heart rate measurements
- **Fields**:
  - Average BPM
  - Min BPM
  - Max BPM
  - Number of measurements
- **Example**: Avg 72 BPM (min: 65, max: 85) over 100 measurements

## 🔧 How It Works

### The Data Flow

```
Android Phone (Health Connect)
    ↓ (auto-exports daily)
Google Drive (healthconnect.zip)
    ↓ (download_health_data.py)
Local: downloaded_data/health_connect_export.db
    ↓ (extract_health_data.py)
Local: extracted_data/health_data_YYYYMMDD.json
    ↓ (import_to_app_db.py)
Your App: data.sqlite
    ↓ (your app reads it)
Beautiful charts! 📈
```

### Database Schema

Your app uses a flexible tracker/entries system:

**Trackers** (like "Steps", "Sleep", "Heart Rate"):
- Define what metrics you're tracking
- Define fields for each metric
- Have icons, colors, descriptions

**Entries** (individual measurements):
- Link to a tracker
- Have a timestamp
- Store the actual data (steps count, sleep hours, etc.)
- Can have notes, tags, duration

### How Import Works

1. **Creates Trackers** (if they don't exist):
   - "Steps" tracker with step count field
   - "Sleep" tracker with duration and stage fields
   - "Heart Rate" tracker with BPM fields

2. **Creates Entries** for each record:
   - Each step record → one entry
   - Each sleep session → one entry
   - Each heart rate record → one entry

3. **Avoids Duplicates**:
   - Uses unique IDs (`hc-steps-123`, etc.)
   - Skips entries that already exist

## 🎓 Learning: How to Add New Data Types

See [HOW_TO_ADD_NEW_DATA_TYPES.md](HOW_TO_ADD_NEW_DATA_TYPES.md) for detailed instructions.

### Quick Summary

1. **Explore** the Health Connect database to find your data:
   ```bash
   sqlite3 downloaded_data/health_connect_export.db ".tables"
   sqlite3 downloaded_data/health_connect_export.db "PRAGMA table_info(TABLE_NAME);"
   ```

2. **Add extraction** in `extract_health_data.py`:
   - Create a function like `extract_weight()`
   - Query the Health Connect database
   - Transform to a clean format
   - Add to the main() function

3. **Add import** in `import_to_app_db.py`:
   - Create a function like `import_weight_data()`
   - Define the tracker (fields, icon, color)
   - Transform to your app's schema
   - Add to the main() function

### Example: Weight Data

```python
# In extract_health_data.py
def extract_weight(db_path, days_back=30):
    # Query weight_record_table
    # Convert grams to kg
    # Return list of weight records

# In import_to_app_db.py
def import_weight_data(cursor, weight_data, dry_run=False):
    # Create "Weight" tracker
    # Import each weight record as an entry
```

## 📈 Available Health Connect Data Types

Here are some interesting data types you can add:

**Activity & Exercise:**
- `exercise_session_record_table` - Workouts with type, duration
- `distance_record_table` - Distance traveled
- `elevation_gained_record_table` - Stairs/elevation
- `active_calories_burned_record_table` - Calories from activity
- `total_calories_burned_record_table` - Total daily calories

**Body Measurements:**
- `weight_record_table` - Body weight
- `height_record_table` - Height
- `body_fat_record_table` - Body fat percentage
- `lean_body_mass_record_table` - Muscle mass
- `bone_mass_record_table` - Bone mass
- `body_water_mass_record_table` - Water weight

**Vital Signs:**
- `blood_pressure_record_table` - BP measurements
- `blood_glucose_record_table` - Blood sugar
- `oxygen_saturation_record_table` - SpO2
- `body_temperature_record_table` - Temperature
- `respiratory_rate_record_table` - Breathing rate
- `resting_heart_rate_record_table` - Resting heart rate
- `heart_rate_variability_rmssd_record_table` - HRV

**Nutrition & Hydration:**
- `nutrition_record_table` - Food/meals with macros
- `hydration_record_table` - Water intake

**Mental & Recovery:**
- `mindfulness_session_record_table` - Meditation
- `vo2_max_record_table` - Cardio fitness

**Women's Health:**
- `menstruation_period_record_table` - Period tracking
- `ovulation_test_record_table` - Ovulation
- `cervical_mucus_record_table` - Fertility signs
- `basal_body_temperature_record_table` - BBT

## 🔄 Automation

### macOS/Linux (cron)

Add to your crontab to run daily at 2 AM:

```bash
crontab -e
```

Add this line:
```
0 2 * * * cd /Users/isaac/Documents/tauri-charts-d3js/charted-health/sync-scripts && /usr/bin/python3 download_health_data.py >> sync.log 2>&1 && /usr/bin/python3 extract_health_data.py >> sync.log 2>&1
```

You'll need to modify `import_to_app_db.py` to run non-interactively (remove the confirmation prompt) if you want it automated.

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task → "Health Connect Sync"
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
   - Program: `python3`
   - Arguments: `download_health_data.py`
   - Start in: `C:\path\to\sync-scripts`
5. Create separate tasks for extract and import

## 🐛 Troubleshooting

### "No module named 'google'"
```bash
python3 -m pip install -r requirements.txt
```

### "Health Connect ZIP file not found"
- Check the exact filename in Google Drive
- Update `HEALTH_CONNECT_ZIP_NAME` in `download_health_data.py` (line 35)

### "Database not found"
Run `download_health_data.py` first to download the database.

### Data not showing in app
1. Check that the import completed successfully
2. Verify entries were created:
   ```bash
   sqlite3 ../data.sqlite "SELECT COUNT(*) FROM entries;"
   sqlite3 ../data.sqlite "SELECT * FROM trackers;"
   ```
3. Restart your app to refresh the UI

### Too much data (slow import)
In `extract_health_data.py`, reduce `days_back`:
```python
days_back = 7  # Instead of 30
```

## 💡 Tips

1. **Start small**: Import 7 days first, then expand to 30 or more
2. **Run extraction separately**: You can run extraction multiple times without re-downloading
3. **Check the JSON**: Review `extracted_data/health_data_*.json` to see what's being imported
4. **Dry run first**: The import script always does a dry run to show what will happen
5. **No duplicates**: Re-running import won't create duplicates
6. **Customize trackers**: Edit the tracker definitions in `import_to_app_db.py` (icons, colors, fields)

## 🎉 What's Next

Now that you have the data flowing:

1. **Build charts** in your Tauri app to visualize the data
2. **Add more metrics** using the guide in `HOW_TO_ADD_NEW_DATA_TYPES.md`
3. **Set up automation** so you don't have to run it manually
4. **Customize the trackers** to match your preferences
5. **Explore the Health Connect data** to find interesting patterns

## 📝 Summary for Teaching

**The Three-File Pattern:**

1. **Extract Function** (`extract_health_data.py`):
   - Connect to Health Connect database
   - Query the table for your metric
   - Transform timestamps, units, etc.
   - Return clean data structure

2. **Import Function** (`import_to_app_db.py`):
   - Define the tracker (fields, icon, color)
   - Create tracker if it doesn't exist
   - For each record, create an entry
   - Skip if entry already exists

3. **Both use the same pattern**:
   - Take the database path
   - Take `days_back` parameter
   - Return/import list of records
   - Print progress messages

**Key Concepts:**

- **Timestamps**: Health Connect uses milliseconds, divide by 1000 for Python
- **Units**: Often metric (grams, meters) - convert as needed
- **Parent/Child Tables**: Some metrics have related tables (like sleep stages)
- **Unique IDs**: Use `hc-METRIC-ROWID` format to prevent duplicates
- **Dry Run**: Always show what will change before actually changing it

You now have a complete, working system! 🚀
