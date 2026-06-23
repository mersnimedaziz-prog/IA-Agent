import os
import json
from datetime import datetime
from monthly_sql_storage import save_result_sql, save_target_sql    



MONTHLY_DATA_DIR = "data/monthly"
IMPORTS_DIR = os.path.join(MONTHLY_DATA_DIR, "imports")
RESULTS_FILE = os.path.join(MONTHLY_DATA_DIR, "monthly_results.json")
TARGETS_FILE = os.path.join(MONTHLY_DATA_DIR, "monthly_targets.json")
ACTIVE_MONTHLY_FILE = os.path.join(MONTHLY_DATA_DIR, "active_monthly_data.xlsx")


# Cache to optimize file loading and avoid wait times
_JSON_CACHE = {}

def ensure_monthly_dirs():
    os.makedirs(IMPORTS_DIR, exist_ok=True)
    os.makedirs(MONTHLY_DATA_DIR, exist_ok=True)


def read_json_file(file_path: str):
    ensure_monthly_dirs()

    if not os.path.exists(file_path):
        return []

    try:
        file_mtime = os.path.getmtime(file_path)
        cache_key = f"{file_path}_{file_mtime}"
        
        if cache_key in _JSON_CACHE:
            return _JSON_CACHE[cache_key]

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        keys_to_remove = [k for k in _JSON_CACHE if k.startswith(f"{file_path}_")]
        for k in keys_to_remove:
            del _JSON_CACHE[k]
            
        _JSON_CACHE[cache_key] = data
        return data
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


def write_json_file(file_path: str, data):
    ensure_monthly_dirs()

    # Atomic write to avoid empty/corrupted files during concurrent reads
    temp_file = file_path + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    os.replace(temp_file, file_path)
    
    # Update cache
    try:
        file_mtime = os.path.getmtime(file_path)
        cache_key = f"{file_path}_{file_mtime}"
        keys_to_remove = [k for k in _JSON_CACHE if k.startswith(f"{file_path}_")]
        for k in keys_to_remove:
            del _JSON_CACHE[k]
        _JSON_CACHE[cache_key] = data
    except Exception:
        pass


def save_monthly_result(month: str, kpi_name: str, value: float, unit: str, total_md=None):
    results = read_json_file(RESULTS_FILE)

    save_result_sql(
    month=month,
    kpi_name=kpi_name,
    value=value,
    unit=unit,
    total_md=total_md
    )


    new_result = {
        "month": month,
        "compilation_date": f"{month}-01",
        "kpi_name": kpi_name,
        "value": value,
        "unit": unit,
        "type": "Result",
        "total_md": total_md,
        "created_at": datetime.now().isoformat()
    }

    results = [
        r for r in results
        if not (r.get("month") == month and r.get("kpi_name") == kpi_name)
    ]

    results.append(new_result)

    write_json_file(RESULTS_FILE, results)

    return new_result


def save_monthly_target(
    month: str,
    kpi_name: str,
    target_value: float,
    unit: str,
    comparison: str = ">=",
    start_date: str = None,
    end_date: str = None
):
    targets = read_json_file(TARGETS_FILE)

    save_target_sql(
    month=month,
    kpi_name=kpi_name,
    target_value=target_value,
    unit=unit,
    comparison=comparison
    )

    new_target = {
        "month": month,
        "compilation_date": f"{month}-01",
        "kpi_name": kpi_name,
        "target_value": target_value,
        "unit": unit,
        "comparison": comparison,
        "start_date": start_date,
        "end_date": end_date,
        "type": "Target",
        "created_at": datetime.now().isoformat()
    }

    targets = [
        t for t in targets
        if not (t.get("month") == month and t.get("kpi_name") == kpi_name)
    ]

    targets.append(new_target)

    write_json_file(TARGETS_FILE, targets)

    return new_target


def get_monthly_results():
    return read_json_file(RESULTS_FILE)


def get_monthly_targets():
    return read_json_file(TARGETS_FILE)


def find_result(month: str, kpi_name: str):
    results = get_monthly_results()

    for result in results:
        if result.get("month") == month and result.get("kpi_name") == kpi_name:
            return result

    return None


def find_target(month: str, kpi_name: str):
    targets = get_monthly_targets()

    for target in targets:
        if target.get("month") == month and target.get("kpi_name") == kpi_name:
            return target

    return None