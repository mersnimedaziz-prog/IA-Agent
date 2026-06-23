import pandas as pd


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

OPTIONAL_COLUMNS = [
    "Parent Epic",
    "Parent Epic Summary",
    "Parent Ticket",
    "Parent Summary",
    "Holiday"
]


def normalize_time_value(value):
    if pd.isna(value):
        return None

    value_str = str(value).strip().replace(",", ".")

    try:
        return float(value_str)
    except Exception:
        return None


def validate_monthly_jira_file(file_path: str) -> dict:
    """
    Valide qu'un fichier Excel respecte la structure attendue
    d'un fichier Jira mensuel.
    """

    validation_errors = []
    validation_warnings = []

    try:
        excel_file = pd.ExcelFile(file_path)
    except Exception:
        return {
            "is_valid": False,
            "errors": [
                "Le fichier ne peut pas être lu comme un fichier Excel valide."
            ],
            "warnings": [],
            "profile": None
        }

    if not excel_file.sheet_names:
        return {
            "is_valid": False,
            "errors": [
                "Le fichier Excel ne contient aucun onglet."
            ],
            "warnings": [],
            "profile": None
        }

    try:
        df = pd.read_excel(file_path, sheet_name=0)
    except Exception:
        return {
            "is_valid": False,
            "errors": [
                "Impossible de lire le premier onglet du fichier Excel."
            ],
            "warnings": [],
            "profile": None
        }

    if df.empty:
        return {
            "is_valid": False,
            "errors": [
                "Le fichier est vide. Aucune donnée Jira n'a été trouvée."
            ],
            "warnings": [],
            "profile": None
        }

    columns = list(df.columns)

    if "Issue key" in columns or "Worklog" in " ".join(columns):
        validation_errors.append(
            "Ce fichier semble être un ancien format Issues/Worklogs. "
            "Veuillez importer un fichier Jira mensuel avec les colonnes Date, Author, Role, Project, Ticket, Summary et Time (h)."
        )

    missing_required_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in columns
    ]

    if missing_required_columns:
        validation_errors.append(
            "Le fichier ne respecte pas la structure Jira attendue. "
            f"Colonnes obligatoires manquantes : {missing_required_columns}"
        )

    missing_optional_columns = [
        column for column in OPTIONAL_COLUMNS
        if column not in columns
    ]

    if missing_optional_columns:
        validation_warnings.append(
            f"Colonnes optionnelles absentes : {missing_optional_columns}"
        )

    # Si les colonnes de base manquent, inutile de continuer les validations de contenu.
    if validation_errors:
        return {
            "is_valid": False,
            "errors": validation_errors,
            "warnings": validation_warnings,
            "profile": {
                "sheet_name": excel_file.sheet_names[0],
                "rows_count": int(len(df)),
                "columns": columns
            }
        }

    # Validation Date
    parsed_dates = pd.to_datetime(df["Date"], errors="coerce")
    invalid_dates_count = int(parsed_dates.isna().sum())

    if invalid_dates_count == len(df):
        validation_errors.append(
            "La colonne Date est invalide. Aucune date exploitable n'a été trouvée."
        )
    elif invalid_dates_count > 0:
        validation_warnings.append(
            f"{invalid_dates_count} ligne(s) contiennent une Date invalide."
        )

    # Validation Started
    parsed_started = pd.to_datetime(df["Started"], errors="coerce")
    invalid_started_count = int(parsed_started.isna().sum())

    if invalid_started_count == len(df):
        validation_warnings.append(
            "La colonne Started ne contient aucune valeur de date exploitable."
        )
    elif invalid_started_count > 0:
        validation_warnings.append(
            f"{invalid_started_count} ligne(s) contiennent une valeur Started invalide."
        )

    # Validation Time (h)
    normalized_hours = df["Time (h)"].apply(normalize_time_value)
    invalid_hours_count = int(normalized_hours.isna().sum())

    if invalid_hours_count == len(df):
        validation_errors.append(
            "La colonne Time (h) est invalide. Aucune valeur horaire exploitable n'a été trouvée."
        )
    elif invalid_hours_count > 0:
        validation_warnings.append(
            f"{invalid_hours_count} ligne(s) contiennent une valeur Time (h) invalide."
        )

    # Validation colonnes textuelles critiques
    critical_text_columns = [
        "Author",
        "Role",
        "Project",
        "Ticket",
        "Summary"
    ]

    for column in critical_text_columns:
        empty_count = int(df[column].isna().sum() + (df[column].astype(str).str.strip() == "").sum())

        if empty_count == len(df):
            validation_errors.append(
                f"La colonne {column} est vide pour toutes les lignes."
            )
        elif empty_count > 0:
            validation_warnings.append(
                f"{empty_count} ligne(s) ont une valeur vide dans la colonne {column}."
            )

    # Validation Weekend
    allowed_weekend_values = {"VRAI", "FAUX", "TRUE", "FALSE", "1", "0", "YES", "NO", ""}
    weekend_values = set(
        df["Weekend"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
        .tolist()
    )

    invalid_weekend_values = [
        value for value in weekend_values
        if value not in allowed_weekend_values
    ]

    if invalid_weekend_values:
        validation_warnings.append(
            f"Valeurs Weekend inhabituelles détectées : {invalid_weekend_values}"
        )

    valid_rows_count = int(
        parsed_dates.notna().sum()
    )

    total_hours = 0.0

    if normalized_hours.notna().any():
        total_hours = round(float(normalized_hours.fillna(0).sum()), 2)

    min_date = None
    max_date = None

    if parsed_dates.notna().any():
        min_date = parsed_dates.min().strftime("%Y-%m-%d")
        max_date = parsed_dates.max().strftime("%Y-%m-%d")

    profile = {
        "sheet_name": excel_file.sheet_names[0],
        "rows_count": int(len(df)),
        "valid_rows_count": valid_rows_count,
        "columns": columns,
        "total_hours": total_hours,
        "min_date": min_date,
        "max_date": max_date,
        "missing_optional_columns": missing_optional_columns
    }

    return {
        "is_valid": len(validation_errors) == 0,
        "errors": validation_errors,
        "warnings": validation_warnings,
        "profile": profile
    }
