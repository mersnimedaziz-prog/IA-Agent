import os
import shutil
from fastapi import APIRouter, File, UploadFile
from kpi_engine import compute_kpis, get_charts_data
from timesheet_validator import clear_validation_cache

router = APIRouter(prefix="/api", tags=["dashboard"])

DATA_DIR = "data"
ACTIVE_FILE = "active_data.xlsx"

@router.post("/upload")
def upload_file(file: UploadFile = File(...)):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if not file.filename.lower().endswith((".xlsx", ".xls")):
            return {
                "error": "Format non supporté. Veuillez importer un fichier Excel .xlsx ou .xls"
            }

        file_path = os.path.join(DATA_DIR, ACTIVE_FILE)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except PermissionError:
            return {
                "error": (
                    "Le fichier active_data.xlsx est actuellement utilisé par un autre processus. "
                    "Fermez Excel ou redémarrez le backend, puis réessayez."
                )
            }

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        clear_validation_cache()

        return {
            "message": f"Le fichier '{file.filename}' a été importé avec succès.",
            "active_file": ACTIVE_FILE
        }

    except Exception as e:
        return {
            "error": f"Erreur pendant l'import du fichier : {str(e)}"
        }

    finally:
        file.file.close()

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "KPI Dashboard API fonctionne correctement"
    }

@router.get("/kpis")
def get_delivery_kpis():
    return compute_kpis()

@router.get("/charts")
def get_dashboard_charts():
    return get_charts_data()
