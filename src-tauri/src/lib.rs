use rusqlite::Connection;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
struct StepsData {
    date: String,
    steps: i64,
}

#[derive(Debug, Serialize, Deserialize)]
struct SleepData {
    date: String,
    duration_hours: f64,
    light_sleep: f64,
    deep_sleep: f64,
    rem_sleep: f64,
    awake_minutes: f64,
    start_datetime: String,
    end_datetime: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct HeartRateData {
    date: String,
    avg_bpm: f64,
    min_bpm: i64,
    max_bpm: i64,
}

#[derive(Debug, Serialize, Deserialize)]
struct WeightData {
    date: String,
    weight_kg: f64,
    weight_lbs: f64,
}

#[derive(Debug, Serialize, Deserialize)]
struct DailyNutritionData {
    date: String,
    total_calories: f64,
    total_protein: f64,
    total_carbs: f64,
    total_fat: f64,
    total_fiber: f64,
    meal_count: i64,
}

#[derive(Debug, Serialize, Deserialize)]
struct NutritionMeal {
    timestamp: String,
    meal_name: String,
    meal_type: String,
    calories: f64,
    protein_g: f64,
    carbs_g: f64,
    fat_g: f64,
    fiber_g: f64,
    sugar_g: f64,
}

fn get_db_path() -> PathBuf {
    // Try multiple locations for the database
    // 1. Project root (for development)
    let project_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join("data.sqlite");

    if project_root.exists() {
        return project_root;
    }

    // 2. Current directory (fallback)
    let current_dir = std::env::current_dir().unwrap().join("data.sqlite");
    current_dir
}

#[tauri::command]
fn get_steps_data(days: Option<u32>) -> Result<Vec<StepsData>, String> {
    let days = days.unwrap_or(30);
    let db_path = get_db_path();

    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;

    let mut stmt = conn.prepare(
        "SELECT
            DATE(timestamp) as date,
            SUM(CAST(json_extract(data, '$.steps') AS INTEGER)) as total_steps
         FROM entries
         WHERE tracker_id = 'health-connect-steps'
           AND timestamp >= datetime('now', '-' || ? || ' days')
         GROUP BY DATE(timestamp)
         ORDER BY date DESC"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let steps_iter = stmt.query_map([days], |row| {
        Ok(StepsData {
            date: row.get(0)?,
            steps: row.get(1)?,
        })
    }).map_err(|e| format!("Failed to query: {}", e))?;

    let mut results = Vec::new();
    for step in steps_iter {
        results.push(step.map_err(|e| format!("Failed to read row: {}", e))?);
    }

    Ok(results)
}

#[tauri::command]
fn get_sleep_data(days: Option<u32>) -> Result<Vec<SleepData>, String> {
    let days = days.unwrap_or(30);
    let db_path = get_db_path();

    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;

    let mut stmt = conn.prepare(
        "SELECT
            DATE(timestamp) as date,
            CAST(json_extract(data, '$.duration_hours') AS REAL) as duration_hours,
            CAST(json_extract(data, '$.light_sleep_minutes') AS REAL) as light_sleep,
            CAST(json_extract(data, '$.deep_sleep_minutes') AS REAL) as deep_sleep,
            CAST(json_extract(data, '$.rem_sleep_minutes') AS REAL) as rem_sleep,
            CAST(json_extract(data, '$.awake_minutes') AS REAL) as awake_minutes,
            timestamp as start_datetime,
            datetime(timestamp, '+' || CAST(json_extract(data, '$.duration_hours') AS INTEGER) || ' hours') as end_datetime
         FROM entries
         WHERE tracker_id = 'health-connect-sleep'
           AND timestamp >= datetime('now', '-' || ? || ' days')
         ORDER BY date DESC"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let sleep_iter = stmt.query_map([days], |row| {
        Ok(SleepData {
            date: row.get(0)?,
            duration_hours: row.get(1)?,
            light_sleep: row.get(2)?,
            deep_sleep: row.get(3)?,
            rem_sleep: row.get(4)?,
            awake_minutes: row.get(5)?,
            start_datetime: row.get(6)?,
            end_datetime: row.get(7)?,
        })
    }).map_err(|e| format!("Failed to query: {}", e))?;

    let mut results = Vec::new();
    for sleep in sleep_iter {
        results.push(sleep.map_err(|e| format!("Failed to read row: {}", e))?);
    }

    Ok(results)
}

#[tauri::command]
fn get_heart_rate_data(days: Option<u32>) -> Result<Vec<HeartRateData>, String> {
    let days = days.unwrap_or(7);  // Default to 7 days for heart rate (lots of data)
    let db_path = get_db_path();

    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;

    let mut stmt = conn.prepare(
        "SELECT
            DATE(timestamp) as date,
            AVG(CAST(json_extract(data, '$.avg_bpm') AS REAL)) as avg_bpm,
            MIN(CAST(json_extract(data, '$.min_bpm') AS INTEGER)) as min_bpm,
            MAX(CAST(json_extract(data, '$.max_bpm') AS INTEGER)) as max_bpm
         FROM entries
         WHERE tracker_id = 'health-connect-heart-rate'
           AND timestamp >= datetime('now', '-' || ? || ' days')
         GROUP BY DATE(timestamp)
         ORDER BY date DESC"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let hr_iter = stmt.query_map([days], |row| {
        Ok(HeartRateData {
            date: row.get(0)?,
            avg_bpm: row.get(1)?,
            min_bpm: row.get(2)?,
            max_bpm: row.get(3)?,
        })
    }).map_err(|e| format!("Failed to query: {}", e))?;

    let mut results = Vec::new();
    for hr in hr_iter {
        results.push(hr.map_err(|e| format!("Failed to read row: {}", e))?);
    }

    Ok(results)
}

#[tauri::command]
fn get_weight_data(days: Option<u32>) -> Result<Vec<WeightData>, String> {
    let days = days.unwrap_or(90);  // Default to 90 days for weight
    let db_path = get_db_path();

    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;

    let mut stmt = conn.prepare(
        "SELECT
            DATE(timestamp) as date,
            CAST(json_extract(data, '$.weight_kg') AS REAL) as weight_kg,
            CAST(json_extract(data, '$.weight_lbs') AS REAL) as weight_lbs
         FROM entries
         WHERE tracker_id = 'health-connect-weight'
           AND timestamp >= datetime('now', '-' || ? || ' days')
         ORDER BY date DESC"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let weight_iter = stmt.query_map([days], |row| {
        Ok(WeightData {
            date: row.get(0)?,
            weight_kg: row.get(1)?,
            weight_lbs: row.get(2)?,
        })
    }).map_err(|e| format!("Failed to query: {}", e))?;

    let mut results = Vec::new();
    for weight in weight_iter {
        results.push(weight.map_err(|e| format!("Failed to read row: {}", e))?);
    }

    Ok(results)
}

#[tauri::command]
fn get_daily_nutrition_data(days: Option<u32>) -> Result<Vec<DailyNutritionData>, String> {
    let days = days.unwrap_or(90);
    let db_path = get_db_path();

    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;

    let mut stmt = conn.prepare(
        "SELECT
            DATE(timestamp) as date,
            SUM(CAST(json_extract(data, '$.calories') AS REAL)) as total_calories,
            SUM(CAST(json_extract(data, '$.protein_g') AS REAL)) as total_protein,
            SUM(CAST(json_extract(data, '$.carbs_g') AS REAL)) as total_carbs,
            SUM(CAST(json_extract(data, '$.fat_g') AS REAL)) as total_fat,
            SUM(CAST(json_extract(data, '$.fiber_g') AS REAL)) as total_fiber,
            COUNT(*) as meal_count
         FROM entries
         WHERE tracker_id = 'health-connect-nutrition'
           AND timestamp >= datetime('now', '-' || ? || ' days')
         GROUP BY DATE(timestamp)
         ORDER BY date DESC"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let nutrition_iter = stmt.query_map([days], |row| {
        Ok(DailyNutritionData {
            date: row.get(0)?,
            total_calories: row.get(1)?,
            total_protein: row.get(2)?,
            total_carbs: row.get(3)?,
            total_fat: row.get(4)?,
            total_fiber: row.get(5)?,
            meal_count: row.get(6)?,
        })
    }).map_err(|e| format!("Failed to query: {}", e))?;

    let mut results = Vec::new();
    for nutrition in nutrition_iter {
        results.push(nutrition.map_err(|e| format!("Failed to read row: {}", e))?);
    }

    Ok(results)
}

#[tauri::command]
fn get_nutrition_meals(days: Option<u32>) -> Result<Vec<NutritionMeal>, String> {
    let days = days.unwrap_or(7);
    let db_path = get_db_path();

    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;

    let mut stmt = conn.prepare(
        "SELECT
            timestamp,
            json_extract(data, '$.meal_name') as meal_name,
            json_extract(data, '$.meal_type') as meal_type,
            CAST(json_extract(data, '$.calories') AS REAL) as calories,
            CAST(json_extract(data, '$.protein_g') AS REAL) as protein_g,
            CAST(json_extract(data, '$.carbs_g') AS REAL) as carbs_g,
            CAST(json_extract(data, '$.fat_g') AS REAL) as fat_g,
            CAST(json_extract(data, '$.fiber_g') AS REAL) as fiber_g,
            CAST(json_extract(data, '$.sugar_g') AS REAL) as sugar_g
         FROM entries
         WHERE tracker_id = 'health-connect-nutrition'
           AND timestamp >= datetime('now', '-' || ? || ' days')
         ORDER BY timestamp DESC"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;

    let meals_iter = stmt.query_map([days], |row| {
        Ok(NutritionMeal {
            timestamp: row.get(0)?,
            meal_name: row.get(1)?,
            meal_type: row.get(2)?,
            calories: row.get(3)?,
            protein_g: row.get(4)?,
            carbs_g: row.get(5)?,
            fat_g: row.get(6)?,
            fiber_g: row.get(7)?,
            sugar_g: row.get(8)?,
        })
    }).map_err(|e| format!("Failed to query: {}", e))?;

    let mut results = Vec::new();
    for meal in meals_iter {
        results.push(meal.map_err(|e| format!("Failed to read row: {}", e))?);
    }

    Ok(results)
}

#[tauri::command]
fn sync_health_data() -> Result<String, String> {
    use std::process::Command;

    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let project_root = manifest_dir
        .parent()
        .ok_or("Failed to get project root")?;

    let sync_scripts = project_root.join("sync-scripts");

    // Run the sync pipeline
    let output = Command::new("sh")
        .current_dir(&sync_scripts)
        .arg("-c")
        .arg("python3 download_health_data.py && python3 extract_health_data.py && python3 import_to_app_db.py --auto")
        .output()
        .map_err(|e| format!("Failed to run sync: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

// Old greet command (keeping for reference)
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            get_steps_data,
            get_sleep_data,
            get_heart_rate_data,
            get_weight_data,
            get_daily_nutrition_data,
            get_nutrition_meals,
            sync_health_data
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
