import pandas as pd
import re

WORKING_HOURS_PER_MD = 8


REQUIRED_COLUMNS = [
    "Date",
    "Author",
    "Role",
    "Project",
    "Ticket",
    "Summary",
    "Time (h)",
    "Status",
    "Started",
    "Weekend"
]


def normalize_time_value(value):
    if pd.isna(value):
        return 0.0

    value_str = str(value).strip().replace(",", ".")

    try:
        return float(value_str)
    except Exception:
        return 0.0


def load_monthly_jira_file(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path)

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Colonnes manquantes : {missing_columns}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Started"] = pd.to_datetime(df["Started"], errors="coerce")
    df["Time_Hours"] = df["Time (h)"].apply(normalize_time_value)

    return df


def filter_by_month(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """
    month format attendu : YYYY-MM
    Exemple : 2026-06
    """
    return filter_by_date_range(df, month)


def filter_by_date_range(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> pd.DataFrame:
    """
    Filtre les données par mois, puis optionnellement par date début / date fin.

    month format : YYYY-MM
    start_date format : YYYY-MM-DD
    end_date format : YYYY-MM-DD
    """
    df = df.copy()

    df["Month"] = df["Date"].dt.strftime("%Y-%m")
    df_month = df[df["Month"] == month].copy()

    if start_date:
        start = pd.to_datetime(start_date, errors="coerce")
        df_month = df_month[df_month["Date"] >= start]

    if end_date:
        end = pd.to_datetime(end_date, errors="coerce")
        df_month = df_month[df_month["Date"] <= end]

    return df_month.copy()


def compute_monthly_total_hours(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> dict:
    df_month = filter_by_date_range(df, month, start_date, end_date)

    total_hours = float(df_month["Time_Hours"].sum())
    total_md = round(total_hours / WORKING_HOURS_PER_MD, 2)

    return {
        "month": month,
        "period_start": start_date,
        "period_end": end_date,
        "kpi_name": "monthly_total_hours",
        "value": round(total_hours, 2),
        "unit": "hours",
        "total_md": total_md,
        "rows_count": int(len(df_month))
    }


def compute_by_role(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> list:
    df_month = filter_by_date_range(df, month, start_date, end_date)

    if df_month.empty:
        return []

    result = (
        df_month
        .groupby("Role")["Time_Hours"]
        .sum()
        .reset_index()
        .sort_values("Time_Hours", ascending=False)
    )

    result["Total_MD"] = (result["Time_Hours"] / WORKING_HOURS_PER_MD).round(2)

    return result.to_dict(orient="records")


def compute_by_author(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> list:
    df_month = filter_by_date_range(df, month, start_date, end_date)

    if df_month.empty:
        return []

    result = (
        df_month
        .groupby("Author")["Time_Hours"]
        .sum()
        .reset_index()
        .sort_values("Time_Hours", ascending=False)
    )

    result["Total_MD"] = (result["Time_Hours"] / WORKING_HOURS_PER_MD).round(2)

    return result.to_dict(orient="records")


def compute_by_project(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> list:
    df_month = filter_by_date_range(df, month, start_date, end_date)

    if df_month.empty:
        return []

    result = (
        df_month
        .groupby("Project")["Time_Hours"]
        .sum()
        .reset_index()
        .sort_values("Time_Hours", ascending=False)
    )

    result["Total_MD"] = (result["Time_Hours"] / WORKING_HOURS_PER_MD).round(2)

    return result.to_dict(orient="records")


def compute_daily_role_pivot(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> list:
    df_month = filter_by_date_range(df, month, start_date, end_date)

    if df_month.empty:
        return []

    df_month["Date_Str"] = df_month["Date"].dt.strftime("%Y-%m-%d")

    pivot = pd.pivot_table(
        df_month,
        index="Role",
        columns="Date_Str",
        values="Time_Hours",
        aggfunc="sum",
        fill_value=0
    )

    pivot["Total"] = pivot.sum(axis=1)
    pivot["Total MD"] = (pivot["Total"] / WORKING_HOURS_PER_MD).round(2)

    pivot = pivot.reset_index()

    return pivot.to_dict(orient="records")


def compare_with_target(result_value: float, target_value: float, comparison: str) -> dict:
    if comparison == ">=":
        achieved = result_value >= target_value
    elif comparison == "<=":
        achieved = result_value <= target_value
    elif comparison == "=":
        achieved = result_value == target_value
    else:
        achieved = False

    gap = round(result_value - target_value, 2)

    return {
        "result": result_value,
        "target": target_value,
        "comparison": comparison,
        "achieved": achieved,
        "gap": gap,
        "status": "Atteint" if achieved else "Non atteint"
    }

def summarize_text_items(items, max_items=5):
    """
    Regroupe les textes Summary en une liste courte.
    On évite les doublons et on limite le nombre d'éléments affichés.
    """
    cleaned = []

    for item in items:
        if pd.isna(item):
            continue

        text = str(item).strip()

        if not text:
            continue

        if text not in cleaned:
            cleaned.append(text)

    return cleaned[:max_items]

def compute_daily_summary(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> list:
    """
    Calcule le total par journée et extrait les activités principales depuis Summary.
    """
    df_month = filter_by_date_range(df, month, start_date, end_date)

    if df_month.empty:
        return []

    grouped_rows = []

    for date_value, group in df_month.groupby(df_month["Date"].dt.strftime("%Y-%m-%d")):
        total_hours = float(group["Time_Hours"].sum())
        total_md = round(total_hours / WORKING_HOURS_PER_MD, 2)

        summaries = summarize_text_items(group["Summary"].tolist(), max_items=6)

        grouped_rows.append({
            "Date": date_value,
            "Total_Hours": round(total_hours, 2),
            "Total_MD": total_md,
            "Activities": summaries,
            "Activities_Text": " | ".join(summaries),
            "Rows_Count": int(len(group))
        })

    return grouped_rows

def compute_role_work_summary(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> list:
    """
    Calcule le total par rôle et indique sur quoi chaque rôle a travaillé
    à partir de la colonne Summary.
    """
    df_month = filter_by_date_range(df, month, start_date, end_date)

    if df_month.empty:
        return []

    grouped_rows = []

    for role, group in df_month.groupby("Role"):
        total_hours = float(group["Time_Hours"].sum())
        total_md = round(total_hours / WORKING_HOURS_PER_MD, 2)

        summaries = summarize_text_items(group["Summary"].tolist(), max_items=8)

        grouped_rows.append({
            "Role": role,
            "Total_Hours": round(total_hours, 2),
            "Total_MD": total_md,
            "Worked_On": summaries,
            "Worked_On_Text": " | ".join(summaries),
            "Tickets_Count": int(group["Ticket"].nunique()) if "Ticket" in group.columns else int(len(group))
        })

    grouped_rows = sorted(grouped_rows, key=lambda x: x["Total_Hours"], reverse=True)

    return grouped_rows

def compute_author_work_summary(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> list:
    """
    Calcule le total par individu et indique sur quoi chaque personne a travaillé
    à partir de la colonne Summary.
    """
    df_month = filter_by_date_range(df, month, start_date, end_date)

    if df_month.empty:
        return []

    grouped_rows = []

    for author, group in df_month.groupby("Author"):
        total_hours = float(group["Time_Hours"].sum())
        total_md = round(total_hours / WORKING_HOURS_PER_MD, 2)

        role = ""
        if "Role" in group.columns and not group["Role"].dropna().empty:
            role = str(group["Role"].dropna().iloc[0])

        summaries = summarize_text_items(group["Summary"].tolist(), max_items=8)

        grouped_rows.append({
            "Author": author,
            "Role": role,
            "Total_Hours": round(total_hours, 2),
            "Total_MD": total_md,
            "Worked_On": summaries,
            "Worked_On_Text": " | ".join(summaries),
            "Tickets_Count": int(group["Ticket"].nunique()) if "Ticket" in group.columns else int(len(group))
        })

    grouped_rows = sorted(grouped_rows, key=lambda x: x["Total_Hours"], reverse=True)

    return grouped_rows


def extract_tags_from_summary(summary: str) -> list:
    """
    Extrait les tags entre crochets depuis Summary.
    Exemple :
    [RB][FE][KYC] Build form -> ["RB", "FE", "KYC"]
    """
    if pd.isna(summary):
        return []

    summary = str(summary).strip()

    tags = re.findall(r"\[([^\]]+)\]", summary)

    return [tag.strip() for tag in tags if tag.strip()]


def clean_summary_text(text: str) -> str:
    """
    Supprime les tags du début du Summary pour afficher une activité lisible.
    Exemple :
    [RB][FE][KYC] Build form -> Build form
    """
    if pd.isna(text):
        return ""

    text = str(text).strip()
    text = re.sub(r"^(\[[^\]]+\])+", "", text).strip()

    return text


def classify_work_item(row) -> dict:
    """
    Classifie une ligne Jira selon les tags Summary, Weekend et Holiday.
    """
    summary = row.get("Summary", "")
    role = row.get("Role", "")
    holiday = row.get("Holiday", "")
    weekend = row.get("Weekend", "")
    status = row.get("Status", "")

    tags = extract_tags_from_summary(summary)

    normalized_tags = [tag.upper() for tag in tags]

    classification = {
        "tags": tags,
        "business_domain": None,
        "role_tag": None,
        "module": None,
        "activity_type": "Regular Work"
    }

    # Domaine métier
    if "RB" in normalized_tags:
        classification["business_domain"] = "RB"

    # Classification rôle depuis tags
    if "FE" in normalized_tags:
        classification["role_tag"] = "FE"
    elif "BE" in normalized_tags:
        classification["role_tag"] = "BE"
    elif "QA" in normalized_tags:
        classification["role_tag"] = "QA"
    elif pd.notna(role) and str(role).strip():
        classification["role_tag"] = str(role).strip()

    # Module fonctionnel
    if "KYC" in normalized_tags:
        classification["module"] = "KYC"
    elif "CONTACTS" in normalized_tags:
        classification["module"] = "Contacts"
    elif "CONTACT" in normalized_tags:
        classification["module"] = "Contacts"

    # Weekend
    if str(weekend).strip().upper() in ["VRAI", "TRUE", "YES", "1"]:
        classification["activity_type"] = "Weekend Work"

    # Public holiday
    if pd.notna(holiday) and str(holiday).strip():
        classification["activity_type"] = "Public Holiday"

    # Si Summary contient directement Public holiday
    if "public holiday" in str(summary).lower():
        classification["activity_type"] = "Public Holiday"

    # Si Summary contient weekend
    if "weekend" in str(summary).lower():
        classification["activity_type"] = "Weekend Work"

    # Si status est Holiday
    if str(status).strip().lower() == "holiday":
        classification["activity_type"] = "Public Holiday"

    return classification


def compute_group_classification(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> list:
    """
    Classifie les groupes/rôles selon les tags et les Summary.
    """
    df_month = filter_by_date_range(df, month, start_date, end_date)

    if df_month.empty:
        return []

    df_month = df_month.copy()
    df_month["Classification"] = df_month.apply(classify_work_item, axis=1)

    grouped_rows = []

    for role, group in df_month.groupby("Role"):
        total_hours = float(group["Time_Hours"].sum())
        total_md = round(total_hours / WORKING_HOURS_PER_MD, 2)

        all_tags = []
        modules = []
        activity_types = []
        activities = []

        for _, row in group.iterrows():
            classification = row["Classification"]

            all_tags.extend(classification.get("tags", []))

            if classification.get("module"):
                modules.append(classification.get("module"))

            if classification.get("activity_type"):
                activity_types.append(classification.get("activity_type"))

            clean_summary = clean_summary_text(row.get("Summary", ""))

            if clean_summary and clean_summary not in activities:
                activities.append(clean_summary)

        grouped_rows.append({
            "Role": role,
            "Total_Hours": round(total_hours, 2),
            "Total_MD": total_md,
            "Tags": sorted(list(set(all_tags))),
            "Modules": sorted(list(set(modules))),
            "Activity_Types": sorted(list(set(activity_types))),
            "Activities": activities[:8],
            "Tickets_Count": int(group["Ticket"].nunique()) if "Ticket" in group.columns else int(len(group))
        })

    grouped_rows = sorted(grouped_rows, key=lambda x: x["Total_Hours"], reverse=True)

    return grouped_rows


def compute_author_classification(
    df: pd.DataFrame,
    month: str,
    start_date: str = None,
    end_date: str = None
) -> list:
    """
    Classifie chaque individu selon les tags et les Summary.
    """
    df_month = filter_by_date_range(df, month, start_date, end_date)

    if df_month.empty:
        return []

    df_month = df_month.copy()
    df_month["Classification"] = df_month.apply(classify_work_item, axis=1)

    grouped_rows = []

    for author, group in df_month.groupby("Author"):
        total_hours = float(group["Time_Hours"].sum())
        total_md = round(total_hours / WORKING_HOURS_PER_MD, 2)

        role = ""
        if "Role" in group.columns and not group["Role"].dropna().empty:
            role = str(group["Role"].dropna().iloc[0])

        all_tags = []
        modules = []
        activity_types = []
        activities = []

        for _, row in group.iterrows():
            classification = row["Classification"]

            all_tags.extend(classification.get("tags", []))

            if classification.get("module"):
                modules.append(classification.get("module"))

            if classification.get("activity_type"):
                activity_types.append(classification.get("activity_type"))

            clean_summary = clean_summary_text(row.get("Summary", ""))

            if clean_summary and clean_summary not in activities:
                activities.append(clean_summary)

        grouped_rows.append({
            "Author": author,
            "Role": role,
            "Total_Hours": round(total_hours, 2),
            "Total_MD": total_md,
            "Tags": sorted(list(set(all_tags))),
            "Modules": sorted(list(set(modules))),
            "Activity_Types": sorted(list(set(activity_types))),
            "Activities": activities[:8],
            "Tickets_Count": int(group["Ticket"].nunique()) if "Ticket" in group.columns else int(len(group))
        })

    grouped_rows = sorted(grouped_rows, key=lambda x: x["Total_Hours"], reverse=True)

    return grouped_rows