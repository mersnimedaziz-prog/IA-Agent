from config import settings
from llm.ollama_client import OllamaClient
from llm.prompt_builder import (
    build_timesheet_explanation_prompt,
    build_kpi_summary_prompt
)


class LLMService:
    def __init__(self):
        self.client = OllamaClient(
            model_name=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_URL
        )

    def check_status(self) -> dict:
        if not settings.USE_OLLAMA:
            return {
                "ollama_available": False,
                "ollama_enabled": False,
                "message": "Ollama est désactivé temporairement dans la configuration.",
                "model": settings.OLLAMA_MODEL,
                "base_url": settings.OLLAMA_URL
            }

        available = self.client.is_available()

        return {
            "ollama_available": available,
            "ollama_enabled": True,
            "model": settings.OLLAMA_MODEL,
            "base_url": settings.OLLAMA_URL
        }

    def explain_timesheet(self, validation_result: dict) -> str:
        if not settings.USE_OLLAMA:
            return (
                "L’explication IA générative via Ollama est désactivée temporairement. "
                "La validation reste disponible via les règles métier et le NLP local."
            )

        if not self.client.is_available():
            return "Le service IA local Ollama n'est pas disponible."

        prompt = build_timesheet_explanation_prompt(validation_result)
        return self.client.generate(prompt)

    def summarize_kpis(self, kpis: dict, charts: dict = None, validations: list = None) -> str:
        if not settings.USE_OLLAMA:
            return (
                "Le résumé IA génératif via Ollama est désactivé temporairement. "
                "Les KPI restent disponibles via le moteur analytique."
            )

        if not self.client.is_available():
            return "Le service IA local Ollama n'est pas disponible."

        prompt = build_kpi_summary_prompt(kpis, charts, validations)
        return self.client.generate(prompt)