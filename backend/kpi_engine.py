import pandas as pd
from data_loader import load_issues, load_worklogs


DONE_STATUSES = ["Done", "Closed"]


def compute_kpis():
    try:
        df_issues = load_issues()

        required_columns = ["Created", "Updated", "Status"]
        missing_columns = [col for col in required_columns if col not in df_issues.columns]

        if missing_columns:
            return {
                "error": f"Colonnes manquantes dans l'onglet Issues : {missing_columns}"
            }

        df_issues["Created"] = pd.to_datetime(df_issues["Created"], errors="coerce")
        df_issues["Updated"] = pd.to_datetime(df_issues["Updated"], errors="coerce")

        df_done = df_issues[df_issues["Status"].isin(DONE_STATUSES)].copy()

        throughput = len(df_done)

        if not df_done.empty:
            df_done["Lead_Time_Days"] = (
                df_done["Updated"] - df_done["Created"]
            ).dt.days

            avg_lead_time = df_done["Lead_Time_Days"].dropna().mean()
        else:
            avg_lead_time = 0

        if pd.isna(avg_lead_time):
            avg_lead_time = 0

        return {
            "throughput": int(throughput),
            "lead_time": round(float(avg_lead_time), 1)
        }

    except Exception as e:
        return {
            "error": f"Erreur de calcul KPI : {str(e)}"
        }


def get_charts_data():
    try:
        df_worklogs = load_worklogs()
        df_issues = load_issues()

        # -------- Graphique 1 : Workload par auteur --------
        if "Author" not in df_worklogs.columns:
            return {"error": "Colonne 'Author' introuvable dans Worklogs"}

        if "Time_Spent_h" in df_worklogs.columns:
            col_hrs = "Time_Spent_h"
        elif "Time_Spent_hrs" in df_worklogs.columns:
            col_hrs = "Time_Spent_hrs"
        else:
            return {
                "error": "Colonne de temps introuvable. Attendu : Time_Spent_h ou Time_Spent_hrs"
            }

        df_worklogs[col_hrs] = pd.to_numeric(df_worklogs[col_hrs], errors="coerce").fillna(0)

        df_workload = (
            df_worklogs
            .groupby("Author")[col_hrs]
            .sum()
            .reset_index()
            .sort_values(col_hrs, ascending=False)
        )

        # -------- Graphique 2 : Throughput par semaine --------
        required_issue_columns = ["Updated", "Status"]
        missing_columns = [col for col in required_issue_columns if col not in df_issues.columns]

        if missing_columns:
            return {
                "error": f"Colonnes manquantes dans Issues : {missing_columns}"
            }

        df_issues["Updated"] = pd.to_datetime(df_issues["Updated"], errors="coerce")

        df_done = (
            df_issues[df_issues["Status"].isin(DONE_STATUSES)]
            .dropna(subset=["Updated"])
            .copy()
        )

        if not df_done.empty:
            df_done["Week"] = df_done["Updated"].dt.strftime("%Y-W%V")
            df_throughput = (
                df_done
                .groupby("Week")
                .size()
                .reset_index(name="Count")
                .sort_values("Week")
                .tail(4)
            )
        else:
            df_throughput = pd.DataFrame(columns=["Week", "Count"])

        return {
            "workload": {
                "labels": df_workload["Author"].astype(str).tolist(),
                "data": df_workload[col_hrs].astype(float).tolist()
            },
            "throughput": {
                "labels": df_throughput["Week"].astype(str).tolist(),
                "data": df_throughput["Count"].astype(int).tolist()
            }
        }

    except Exception as e:
        return {
            "error": f"Erreur calcul graphiques : {str(e)}"
        }