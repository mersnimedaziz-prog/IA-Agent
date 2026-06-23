import os
import pandas as pd

DATA_DIR = "data"
ACTIVE_FILE = "active_data.xlsx"


def get_active_file_path():
    file_path = os.path.join(DATA_DIR, ACTIVE_FILE)

    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError("Dossier data introuvable")

    if not os.path.exists(file_path):
        fichiers = os.listdir(DATA_DIR)
        raise FileNotFoundError(
            f"Fichier actif '{ACTIVE_FILE}' introuvable. Fichiers trouvés : {fichiers}"
        )

    return file_path


def get_excel_file():
    file_path = get_active_file_path()
    return pd.ExcelFile(file_path), file_path


def find_sheet(xls, keyword: str):
    sheet = next((s for s in xls.sheet_names if keyword.lower() in s.lower()), None)

    if not sheet:
        raise ValueError(
            f"Onglet contenant '{keyword}' introuvable. Onglets trouvés : {xls.sheet_names}"
        )

    return sheet


def load_issues():
    xls, file_path = get_excel_file()
    sheet_issues = find_sheet(xls, "issue")
    df_issues = pd.read_excel(file_path, sheet_name=sheet_issues)
    return df_issues


def load_worklogs():
    xls, file_path = get_excel_file()
    sheet_worklogs = find_sheet(xls, "worklog")
    df_worklogs = pd.read_excel(file_path, sheet_name=sheet_worklogs)
    return df_worklogs


def load_issues_and_worklogs():
    xls, file_path = get_excel_file()

    sheet_issues = find_sheet(xls, "issue")
    sheet_worklogs = find_sheet(xls, "worklog")

    df_issues = pd.read_excel(file_path, sheet_name=sheet_issues)
    df_worklogs = pd.read_excel(file_path, sheet_name=sheet_worklogs)

    return df_issues, df_worklogs