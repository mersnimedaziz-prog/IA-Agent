import pandas as pd
from data_loader import load_issues_and_worklogs


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DONE_STATUSES = ["Done", "Closed"]
SIMILARITY_THRESHOLD = 0.30

_validation_cache = None
_similarity_cache = {}

_nlp_model = None
_nlp_util = None


# ---------------------------------------------------------
# Gestion du cache
# ---------------------------------------------------------

def clear_validation_cache():
    """
    Vide le cache des validations.
    À appeler après chaque nouvel upload Excel.
    """
    global _validation_cache, _similarity_cache

    _validation_cache = None
    _similarity_cache = {}


# ---------------------------------------------------------
# Chargement lazy du modèle NLP
# ---------------------------------------------------------

def get_nlp_model():
    """
    Charge le modèle NLP uniquement au moment où il est nécessaire.
    Cela évite de ralentir ou bloquer le démarrage FastAPI.
    """
    global _nlp_model, _nlp_util

    if _nlp_model is not None and _nlp_util is not None:
        return _nlp_model, _nlp_util

    try:
        #from sentence_transformers import SentenceTransformer, util

        print("Chargement de l'IA NLP en cours...")
        #nlp_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        #_nlp_util = util
        print("IA NLP chargée et prête.")

        return _nlp_model, _nlp_util

    except ModuleNotFoundError:
        raise RuntimeError(
            "Le module 'sentence-transformers' n'est pas installé dans l'environnement Python actif. "
            "Installe-le avec : python -m pip install sentence-transformers"
        )

    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement du modèle NLP : {str(e)}")


# ---------------------------------------------------------
# Helpers colonnes
# ---------------------------------------------------------

def get_hours_column(df_worklogs):
    """
    Détecte la colonne des heures saisies.
    """
    if "Time_Spent_hrs" in df_worklogs.columns:
        return "Time_Spent_hrs"

    if "Time_Spent_h" in df_worklogs.columns:
        return "Time_Spent_h"

    raise ValueError(
        "Colonne de temps introuvable. Colonnes acceptées : Time_Spent_hrs ou Time_Spent_h"
    )


def get_date_column(df_worklogs):
    """
    Détecte la colonne de date du worklog.
    """
    if "Date_Started" in df_worklogs.columns:
        return "Date_Started"

    if "Date_Logged" in df_worklogs.columns:
        return "Date_Logged"

    raise ValueError(
        "Colonne date introuvable. Colonnes acceptées : Date_Started ou Date_Logged"
    )


def safe_str(value):
    """
    Convertit proprement une valeur Pandas en string.
    """
    if pd.isna(value):
        return ""

    return str(value).strip()


def normalize_status(status):
    """
    Normalise le statut Jira.
    """
    if pd.isna(status):
        return ""

    return str(status).strip()


# ---------------------------------------------------------
# Similarité NLP
# ---------------------------------------------------------

def calculate_similarity(summary: str, comment: str) -> float:
    """
    Calcule la similarité sémantique entre le Summary du ticket
    et le commentaire du worklog.

    Retourne un score entre -1 et 1 selon le modèle.
    En pratique :
    - proche de 1 = très similaire
    - proche de 0 = faible similarité
    - inférieur à 0.30 = potentiellement hors sujet dans notre règle métier
    """
    summary = safe_str(summary)
    comment = safe_str(comment)

    if not summary or not comment:
        return 0.0

    cache_key = (summary.lower(), comment.lower())

    if cache_key in _similarity_cache:
        return _similarity_cache[cache_key]

    nlp_model, util = get_nlp_model()

    emb_summary = nlp_model.encode(summary, convert_to_tensor=True)
    emb_comment = nlp_model.encode(comment, convert_to_tensor=True)

    similarity_score = util.cos_sim(emb_summary, emb_comment).item()
    similarity_score = float(similarity_score)

    _similarity_cache[cache_key] = similarity_score

    return similarity_score


# ---------------------------------------------------------
# Scoring d'une ligne worklog
# ---------------------------------------------------------

def calculate_score(row, col_date, col_hrs):
    """
    Calcule le score de cohérence d'un worklog.
    """
    score = 100
    reasons = []
    similarity_score = None

    # -----------------------------------------------------
    # Règle 1 : saisie après fermeture du ticket
    # -----------------------------------------------------
    date_worklog = row.get(col_date)
    updated_date = row.get("Updated")
    status = normalize_status(row.get("Status"))

    if (
        status in DONE_STATUSES
        and pd.notna(date_worklog)
        and pd.notna(updated_date)
        and date_worklog > updated_date
    ):
        score -= 25
        reasons.append("Saisie après la fermeture du ticket")

    # -----------------------------------------------------
    # Règle 2 : volume horaire très élevé
    # -----------------------------------------------------
    hrs = row.get(col_hrs, 0)

    try:
        hrs = float(hrs) if pd.notna(hrs) else 0.0
    except Exception:
        hrs = 0.0

    if hrs > 10:
        score -= 20
        reasons.append(f"Volume très élevé ({hrs}h)")

    # -----------------------------------------------------
    # Règle 3 : commentaire absent ou trop court
    # -----------------------------------------------------
    comment = safe_str(row.get("Comment"))
    summary = safe_str(row.get("Summary"))

    if len(comment) < 5:
        score -= 15
        reasons.append("Commentaire absent ou trop court")

    # -----------------------------------------------------
    # Règle 4 : similarité sémantique entre Summary et Comment
    # -----------------------------------------------------
    elif summary:
        similarity_score = calculate_similarity(summary, comment)

        print(
            f"[{row.get('Issue_Key')}] Score IA : {similarity_score:.2f} | "
            f"Ticket : '{summary}' -> Saisie : '{comment}'"
        )

        if similarity_score < SIMILARITY_THRESHOLD:
            score -= 30
            reasons.append(
                f"IA : commentaire potentiellement hors sujet "
                f"(score de pertinence : {similarity_score:.2f})"
            )

    # -----------------------------------------------------
    # Sécuriser le score final
    # -----------------------------------------------------
    score = max(0, min(100, score))

    if score >= 80:
        decision = "🟢 Valide"
    elif score >= 60:
        decision = "🟡 À vérifier"
    else:
        decision = "🔴 Suspect"

    reasons_text = " | ".join(reasons) if reasons else "Aucune anomalie détectée"

    return pd.Series([
        int(score),
        decision,
        reasons_text,
        similarity_score
    ])


# ---------------------------------------------------------
# Nettoyage JSON
# ---------------------------------------------------------

def clean_records_for_json(records):
    """
    Nettoie les valeurs NaN / NaT pour éviter les problèmes JSON côté Angular.
    """
    cleaned_records = []

    for record in records:
        cleaned_record = {}

        for key, value in record.items():
            if pd.isna(value):
                cleaned_record[key] = None
            else:
                cleaned_record[key] = value

        cleaned_records.append(cleaned_record)

    return cleaned_records


# ---------------------------------------------------------
# Validation principale
# ---------------------------------------------------------

def validate_worklogs():
    """
    Valide les worklogs à partir du fichier Excel actif.
    Retourne une liste de validations exploitable par Angular.
    """
    global _validation_cache

    if _validation_cache is not None:
        return _validation_cache

    try:
        df_issues, df_worklogs = load_issues_and_worklogs()

        # -------------------------------------------------
        # Vérification des colonnes obligatoires
        # -------------------------------------------------
        required_issue_columns = [
            "Issue_Key",
            "Summary",
            "Status",
            "Updated"
        ]

        required_worklog_columns = [
            "Issue_Key",
            "Author",
            "Comment"
        ]

        missing_issue_columns = [
            col for col in required_issue_columns
            if col not in df_issues.columns
        ]

        missing_worklog_columns = [
            col for col in required_worklog_columns
            if col not in df_worklogs.columns
        ]

        if missing_issue_columns:
            return {
                "error": f"Colonnes manquantes dans Issues : {missing_issue_columns}"
            }

        if missing_worklog_columns:
            return {
                "error": f"Colonnes manquantes dans Worklogs : {missing_worklog_columns}"
            }

        col_hrs = get_hours_column(df_worklogs)
        col_date = get_date_column(df_worklogs)

        # -------------------------------------------------
        # Normalisation des types
        # -------------------------------------------------
        df_issues["Updated"] = pd.to_datetime(
            df_issues["Updated"],
            errors="coerce"
        )

        df_worklogs[col_date] = pd.to_datetime(
            df_worklogs[col_date],
            errors="coerce"
        )

        df_worklogs[col_hrs] = pd.to_numeric(
            df_worklogs[col_hrs],
            errors="coerce"
        ).fillna(0)

        # -------------------------------------------------
        # Jointure Worklogs + Issues
        # -------------------------------------------------
        df = pd.merge(
            df_worklogs,
            df_issues,
            on="Issue_Key",
            how="left"
        )

        # -------------------------------------------------
        # Calcul score + décision
        # -------------------------------------------------
        df[["Score", "Decision", "Raisons", "Similarity_Score"]] = df.apply(
            lambda row: calculate_score(row, col_date, col_hrs),
            axis=1
        )

        # -------------------------------------------------
        # Détection colonne ID
        # -------------------------------------------------
        if "Worklog_ID" in df.columns:
            col_id = "Worklog_ID"
        elif "id" in df.columns:
            col_id = "id"
        else:
            df["Generated_ID"] = range(1, len(df) + 1)
            col_id = "Generated_ID"

        result_columns = [
            col_id,
            "Author",
            "Issue_Key",
            "Score",
            "Decision",
            "Raisons",
            "Similarity_Score"
        ]

        result_df = df[result_columns].copy()

        records = result_df.to_dict(orient="records")
        records = clean_records_for_json(records)

        _validation_cache = records

        return _validation_cache

    except Exception as e:
        return {
            "error": f"Erreur de validation timesheets : {str(e)}"
        }