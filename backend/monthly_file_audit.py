import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
import profile

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
MONTHLY_DATA_DIR = BASE_DIR / "data" / "monthly"
IMPORTS_DIR = MONTHLY_DATA_DIR / "imports"
AUDIT_FILE = MONTHLY_DATA_DIR / "monthly_file_audit.json"
ACTIVE_MONTHLY_FILE = MONTHLY_DATA_DIR / "active_monthly_data.xlsx"


def ensure_audit_dirs():
    MONTHLY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)


def compute_file_hash(file_path: str) -> str:
    """
    Calcule le hash SHA256 du fichier.
    Si le hash est identique, le fichier est identique bit par bit.
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def read_audit_history():
    ensure_audit_dirs()

    if not AUDIT_FILE.exists():
        return []

    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def write_audit_history(history):
    ensure_audit_dirs()

    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def normalize_time_value(value):
    if pd.isna(value):
        return 0.0

    value_str = str(value).strip().replace(",", ".")

    try:
        return float(value_str)
    except Exception:
        return 0.0


def load_jira_monthly_df(file_path: str) -> pd.DataFrame:
    """
    Charge le premier onglet du fichier Jira mensuel.
    """
    df = pd.read_excel(file_path, sheet_name=0)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    if "Time (h)" in df.columns:
        df["Time_Hours"] = df["Time (h)"].apply(normalize_time_value)
    else:
        df["Time_Hours"] = 0.0

    return df


def build_file_profile(file_path: str) -> dict:
    """
    Crée un profil métier du fichier :
    - nombre de lignes
    - colonnes
    - total heures
    - période min/max
    - total par rôle
    - total par auteur
    """
    df = load_jira_monthly_df(file_path)

    rows_count = int(len(df))
    columns = list(df.columns)

    total_hours = 0.0
    if "Time_Hours" in df.columns:
        total_hours = round(float(df["Time_Hours"].sum()), 2)

    min_date = None
    max_date = None

    if "Date" in df.columns and not df["Date"].dropna().empty:
        min_date = df["Date"].min().strftime("%Y-%m-%d")
        max_date = df["Date"].max().strftime("%Y-%m-%d")

    by_role = {}
    if "Role" in df.columns and "Time_Hours" in df.columns:
        by_role = (
            df.groupby("Role")["Time_Hours"]
            .sum()
            .round(2)
            .to_dict()
        )

    by_author = {}
    if "Author" in df.columns and "Time_Hours" in df.columns:
        by_author = (
            df.groupby("Author")["Time_Hours"]
            .sum()
            .round(2)
            .to_dict()
        )

    return {
        "rows_count": rows_count,
        "columns": columns,
        "total_hours": total_hours,
        "min_date": min_date,
        "max_date": max_date,
        "by_role": by_role,
        "by_author": by_author
    }


def build_row_key(row) -> str:
    """
    Clé métier approximative pour identifier une ligne.
    Comme ton fichier ne contient pas Worklog_ID, on utilise :
    Date + Author + Ticket + Started

    Si plus tard tu ajoutes Worklog_ID, il faudra l’utiliser à la place.
    """
    date_value = row.get("Date", "")
    author = row.get("Author", "")
    ticket = row.get("Ticket", "")
    started = row.get("Started", "")

    if pd.notna(date_value) and hasattr(date_value, "strftime"):
        date_value = date_value.strftime("%Y-%m-%d")

    return f"{date_value}|{author}|{ticket}|{started}"


def build_row_map(df: pd.DataFrame) -> dict:
    """
    Transforme le DataFrame en dictionnaire indexé par clé métier.
    """
    row_map = {}

    for _, row in df.iterrows():
        key = build_row_key(row)
        row_map[key] = {
            "Date": str(row.get("Date", "")),
            "Author": str(row.get("Author", "")),
            "Role": str(row.get("Role", "")),
            "Ticket": str(row.get("Ticket", "")),
            "Summary": str(row.get("Summary", "")),
            "Time_Hours": float(row.get("Time_Hours", 0) or 0),
            "Status": str(row.get("Status", "")),
            "Started": str(row.get("Started", ""))
        }

    return row_map


def compute_breakdown_gap(old_dict: dict, new_dict: dict) -> list:
    """
    Calcule les écarts d'heures par clé (rôle ou auteur).
    """
    all_keys = set(old_dict.keys()) | set(new_dict.keys())
    gaps = []

    for key in sorted(all_keys):
        old_hours = round(float(old_dict.get(key, 0) or 0), 2)
        new_hours = round(float(new_dict.get(key, 0) or 0), 2)
        gap = round(new_hours - old_hours, 2)

        if gap != 0:
            gaps.append({
                "name": key,
                "old_hours": old_hours,
                "new_hours": new_hours,
                "gap": gap
            })

    gaps.sort(key=lambda item: abs(item["gap"]), reverse=True)
    return gaps


def compare_monthly_files(old_file_path: str, new_file_path: str) -> dict:
    """
    Compare deux fichiers Jira mensuels.
    Retourne un résumé des différences.
    """
    old_df = load_jira_monthly_df(old_file_path)
    new_df = load_jira_monthly_df(new_file_path)

    old_map = build_row_map(old_df)
    new_map = build_row_map(new_df)

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys
    common_keys = old_keys & new_keys

    modified_rows = []

    for key in common_keys:
        old_row = old_map[key]
        new_row = new_map[key]

        changes = {}

        for field in ["Summary", "Time_Hours", "Status", "Role", "Author", "Ticket"]:
            if old_row.get(field) != new_row.get(field):
                changes[field] = {
                    "old": old_row.get(field),
                    "new": new_row.get(field)
                }

        if changes:
            modified_rows.append({
                "row_key": key,
                "changes": changes
            })

    old_profile = build_file_profile(old_file_path)
    new_profile = build_file_profile(new_file_path)

    total_hours_gap = round(
        new_profile["total_hours"] - old_profile["total_hours"],
        2
    )

    by_role_gap = compute_breakdown_gap(
        old_profile.get("by_role", {}),
        new_profile.get("by_role", {})
    )
    by_author_gap = compute_breakdown_gap(
        old_profile.get("by_author", {}),
        new_profile.get("by_author", {})
    )

    return {
        "old_profile": old_profile,
        "new_profile": new_profile,
        "summary": {
            "added_rows_count": len(added_keys),
            "removed_rows_count": len(removed_keys),
            "modified_rows_count": len(modified_rows),
            "old_total_hours": old_profile["total_hours"],
            "new_total_hours": new_profile["total_hours"],
            "total_hours_gap": total_hours_gap,
            "by_role_gap": by_role_gap,
            "by_author_gap": by_author_gap
        },
        "added_rows": [new_map[key] for key in list(added_keys)[:10]],
        "removed_rows": [old_map[key] for key in list(removed_keys)[:10]],
        "modified_rows": modified_rows[:10]
    }


def find_latest_upload_by_filename(original_filename: str):
    """
    Cherche le dernier upload connu pour ce nom de fichier.
    """
    history = read_audit_history()

    matching = [
        item for item in history
        if item.get("original_filename") == original_filename
    ]

    if not matching:
        return None

    matching = sorted(
        matching,
        key=lambda item: item.get("uploaded_at", ""),
        reverse=True
    )

    return matching[0]


def register_monthly_upload(original_filename: str, active_file_path: str) -> dict:
    """
    Enregistre l'upload dans l'historique d'audit.
    """
    ensure_audit_dirs()

    file_hash = compute_file_hash(active_file_path)
    profile = build_file_profile(active_file_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_file_name = f"{timestamp}_{original_filename}"
    archived_file_path = IMPORTS_DIR / archived_file_name

    # Archive une copie du fichier actif.
    with open(active_file_path, "rb") as source:
        with open(archived_file_path, "wb") as destination:
            destination.write(source.read())

    history = read_audit_history()

    upload_id = f"{timestamp}_{file_hash[:8]}"

    audit_item = {
    "upload_id": upload_id,
    "original_filename": original_filename,
    "file_hash": file_hash,
    "active_file_path": str(active_file_path),
    "archived_file_path": str(archived_file_path),
    "uploaded_at": datetime.now().isoformat(),
    "profile": profile
    }
    
    history.append(audit_item)
    write_audit_history(history)

    return audit_item


def save_active_monthly_metadata(original_filename: str) -> dict:
    """
    Sauvegarde les métadonnées du fichier mensuel actif.
    """
    ensure_audit_dirs()

    metadata = {
        "original_filename": original_filename,
        "active_file_path": str(ACTIVE_MONTHLY_FILE),
        "updated_at": datetime.now().isoformat()
    }

    metadata_file = MONTHLY_DATA_DIR / "active_monthly_metadata.json"

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata


def audit_new_monthly_upload(original_filename: str, new_file_path: str) -> dict:
    """
    Compare le nouveau fichier avec le dernier fichier portant le même nom.
    """
    ensure_audit_dirs()

    new_hash = compute_file_hash(new_file_path)
    latest_upload = find_latest_upload_by_filename(original_filename)

    if latest_upload is None:
        return {
            "alert_type": "new_file",
            "severity": "info",
            "title": "Nouveau fichier importé",
            "message": "Ce fichier n’a jamais été importé auparavant.",
            "previous_upload": None,
            "diff": None
        }

    old_hash = latest_upload.get("file_hash")
    old_file_path = latest_upload.get("archived_file_path")

    if old_hash == new_hash:
        profile = latest_upload.get("profile", {})
        rows = profile.get("rows_count", "N/A")
        hours = profile.get("total_hours", "N/A")
        
        upload_date = latest_upload.get("uploaded_at", "")
        if upload_date:
            try:
                dt = datetime.fromisoformat(upload_date)
                upload_date_str = dt.strftime("%d/%m/%Y à %H:%M")
            except Exception:
                upload_date_str = upload_date
        else:
            upload_date_str = "date inconnue"
            
        msg = (
            f"Ce fichier a déjà été importé et aucune modification n'a été détectée.\n"
            f"Détails de l'import précédent (le {upload_date_str}) : "
            f"{rows} lignes, {hours} heures."
        )

        return {
            "alert_type": "same_file",
            "severity": "success",
            "title": "Fichier déjà importé sans modification",
            "message": msg,
            "previous_upload": latest_upload,
            "diff": None
        }

    diff = compare_monthly_files(old_file_path, new_file_path)

    return {
        "alert_type": "modified_file",
        "severity": "warning",
        "title": "Modifications détectées",
        "message": "Ce fichier a déjà été importé auparavant, mais des modifications ont été détectées.",
        "previous_upload": latest_upload,
        "diff": diff
    }