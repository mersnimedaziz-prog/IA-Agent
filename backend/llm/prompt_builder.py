import json


def build_timesheet_explanation_prompt(validation_result: dict) -> str:
    validation_json = json.dumps(
        validation_result,
        ensure_ascii=False,
        indent=2
    )

    return f"""
Tu dois analyser une ligne de validation de timesheet Jira.

Objectif :
Expliquer pourquoi cette saisie est valide, à vérifier ou suspecte.

Contraintes :
- Utilise uniquement les données JSON fournies.
- N'invente aucune information.
- Ne modifie pas le score.
- Ne modifie pas la décision.
- Ne fais pas d'accusation contre l'utilisateur.
- Explique de façon professionnelle.
- Si les données sont insuffisantes, indique que l'analyse est limitée.

Données JSON :
{validation_json}

Réponds exactement avec cette structure :

1. Résumé
2. Faits observés
3. Règles déclenchées
4. Niveau de risque
5. Recommandation
"""

def build_kpi_summary_prompt(kpis: dict, charts: dict = None, validations: list = None) -> str:
    validations = validations if isinstance(validations, list) else []

    valid_count = len([
        v for v in validations
        if "Valide" in str(v.get("Decision", ""))
    ])

    review_count = len([
        v for v in validations
        if "À vérifier" in str(v.get("Decision", ""))
    ])

    suspect_count = len([
        v for v in validations
        if "Suspect" in str(v.get("Decision", ""))
    ])

    total_validations = len(validations)

    context = {
        "definition_des_kpi": {
            "throughput": "Nombre de tickets terminés avec le statut Done ou Closed.",
            "lead_time": "Durée moyenne entre la date de création et la date de clôture/mise à jour d’un ticket terminé. L’unité est le jour.",
            "workload": "Somme des heures saisies dans les worklogs, groupées par auteur.",
            "throughput_par_semaine": "Nombre de tickets terminés par semaine."
        },
        "kpis_observes": {
            "throughput_tickets_termines": kpis.get("throughput"),
            "lead_time_moyen_jours": kpis.get("lead_time")
        },
        "validation_timesheets": {
            "total_lignes_analysees": total_validations,
            "timesheets_valides": valid_count,
            "timesheets_a_verifier": review_count,
            "timesheets_suspectes": suspect_count
        },
        "donnees_graphiques": charts,
        "echantillon_validations": validations[:5]  # Inclure un échantillon des validations pour le contexte
    }

    context_json = json.dumps(
        context,
        ensure_ascii=False,
        indent=2
    )

    return f"""
Tu es un assistant IA local spécialisé dans le pilotage Delivery Jira.

Tu dois générer un résumé professionnel du dashboard à partir du JSON fourni.

Règles strictes :
- N'invente aucune donnée.
- N'invente aucune unité.
- Ne parle jamais d'heures pour le lead time.
- Le lead time est exprimé en jours.
- Le throughput est un nombre de tickets terminés.
- Le workload représente des heures saisies par auteur.
- Ne crée pas de KPI appelé "théorie du temps de livraison".
- Ne dis pas "cases par jour".
- Utilise seulement les chiffres présents dans le JSON.
- Si une information manque, indique que l’analyse est limitée.
- Réponds en français clair, professionnel et concis.
- Ne mets pas de Markdown avec **.
- Utilise des titres simples.

Données JSON :
{context_json}

Réponds exactement avec cette structure :

1. Santé globale du delivery
2. KPI principaux observés
3. État des validations timesheets
4. Points de vigilance
5. Recommandations
"""