import requests


class OllamaClient:
    def __init__(
        self,
        model_name: str = "agent-delivery-kpi",
        base_url: str = "http://localhost:11434"
    ):
        self.model_name = model_name
        self.base_url = base_url
        self.chat_url = f"{self.base_url}/api/chat"
        self.tags_url = f"{self.base_url}/api/tags"

    def is_available(self) -> bool:
        try:
            response = requests.get(self.tags_url, timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 2048,
                "num_predict": 350
            }
        }

        try:
            response = requests.post(
                self.chat_url,
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            return data.get("message", {}).get("content", "Aucune réponse IA générée.")

        except requests.exceptions.Timeout:
            return (
                "Le service IA local a pris trop de temps à répondre. "
                "Veuillez réessayer avec une demande plus courte."
            )

        except requests.exceptions.ConnectionError:
            return (
                "Le service IA local Ollama est indisponible. "
                "Vérifiez qu'Ollama est lancé."
            )

        except Exception as e:
            return f"Erreur lors de l'appel au service IA local : {str(e)}"