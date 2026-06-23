from fastapi import APIRouter
from kpi_engine import compute_kpis, get_charts_data
from timesheet_validator import validate_worklogs
from llm.llm_service import LLMService

router = APIRouter(prefix="/api", tags=["timesheets"])
llm_service = LLMService()

@router.get("/timesheets/validation")
def get_timesheet_validation():
    return validate_worklogs()

@router.get("/ollama/status")
def get_ollama_status():
    return llm_service.check_status()

@router.post("/timesheets/explain")
def explain_timesheet(validation_result: dict):
    try:
        explanation = llm_service.explain_timesheet(validation_result)

        return {
            "score": validation_result.get("Score"),
            "decision": validation_result.get("Decision"),
            "reasons": validation_result.get("Raisons"),
            "ai_explanation": explanation
        }

    except Exception as e:
        return {
            "error": f"Erreur lors de la génération de l'explication IA : {str(e)}"
        }

@router.post("/kpis/summary")
def summarize_dashboard():
    try:
        kpis = compute_kpis()
        charts = get_charts_data()
        validations = validate_worklogs()

        summary = llm_service.summarize_kpis(
            kpis=kpis,
            charts=charts,
            validations=validations if isinstance(validations, list) else []
        )

        return {
            "kpis": kpis,
            "ai_summary": summary
        }

    except Exception as e:
        return {
            "error": f"Erreur lors de la génération du résumé IA : {str(e)}"
        }
