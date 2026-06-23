import os
import shutil
from fastapi import APIRouter, File, UploadFile, Query
from monthly_file_audit import (
    audit_new_monthly_upload,
    save_active_monthly_metadata,
    register_monthly_upload,
    read_audit_history,
    MONTHLY_DATA_DIR
)
from monthly_file_validator import validate_monthly_jira_file
from monthly.monthly_storage import (
    save_monthly_result,
    save_monthly_target,
    get_monthly_results,
    get_monthly_targets,
    find_target,
    find_result,
    ensure_monthly_dirs,
    ACTIVE_MONTHLY_FILE
)
from monthly.monthly_kpi_engine import (
    load_monthly_jira_file,
    compute_monthly_total_hours,
    compute_by_role,
    compute_by_author,
    compute_by_project,
    compute_daily_role_pivot,
    compare_with_target,
    compute_daily_summary,
    compute_role_work_summary,
    compute_author_work_summary,
    compute_group_classification,
    compute_author_classification
)
from monthly.monthly_schemas import TargetRequest, CalculateRequest

router = APIRouter(prefix="/api/monthly", tags=["monthly"])

@router.post("/upload")
def upload_monthly_file(file: UploadFile = File(...)):
    try:
        ensure_monthly_dirs()

        if not file.filename.lower().endswith((".xlsx", ".xls")):
            return {
                "error": "Format non supportÃ©. Veuillez importer un fichier Excel .xlsx ou .xls",
                "validation": {
                    "is_valid": False,
                    "errors": [
                        "Le fichier n'est pas un fichier Excel valide."
                    ],
                    "warnings": []
                }
            }

        temp_file_path = MONTHLY_DATA_DIR / f"temp_{file.filename}"

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        validation_result = validate_monthly_jira_file(str(temp_file_path))

        if not validation_result.get("is_valid"):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

            return {
                "error": "Fichier Jira invalide. Le fichier ne respecte pas la structure attendue.",
                "validation": validation_result
            }

        audit_result = audit_new_monthly_upload(
            original_filename=file.filename,
            new_file_path=str(temp_file_path)
        )

        with open(temp_file_path, "rb") as source:
            with open(ACTIVE_MONTHLY_FILE, "wb") as destination:
                shutil.copyfileobj(source, destination)

        metadata = save_active_monthly_metadata(file.filename)

        audit_item = None
        if audit_result.get("alert_type") != "same_file":
            audit_item = register_monthly_upload(
                original_filename=file.filename,
                active_file_path=str(ACTIVE_MONTHLY_FILE)
            )

        try:
            os.remove(temp_file_path)
        except Exception:
            pass

        return {
            "message": f"Fichier mensuel '{file.filename}' importÃ© avec succÃ¨s.",
            "active_monthly_file": str(ACTIVE_MONTHLY_FILE),
            "metadata": metadata,
            "validation": validation_result,
            "audit": audit_result,
            "audit_item": audit_item
        }

    except Exception as e:
        return {
            "error": f"Erreur pendant l'import mensuel : {str(e)}"
        }

    finally:
        file.file.close()


@router.get("/uploads")
def get_monthly_uploads():
    try:
        history = read_audit_history()

        needs_save = False
        uploads = []

        for item in history:
            profile = item.get("profile", {})

            # Generate upload_id for legacy entries that don't have one
            upload_id = item.get("upload_id")
            if not upload_id:
                import hashlib
                raw = f"{item.get('uploaded_at', '')}_{item.get('original_filename', '')}"
                upload_id = hashlib.md5(raw.encode()).hexdigest()[:16]
                item["upload_id"] = upload_id
                needs_save = True

            uploads.append({
                "upload_id": upload_id,
                "original_filename": item.get("original_filename"),
                "uploaded_at": item.get("uploaded_at"),
                "archived_file_path": item.get("archived_file_path"),
                "rows_count": profile.get("rows_count"),
                "total_hours": profile.get("total_hours"),
                "min_date": profile.get("min_date"),
                "max_date": profile.get("max_date"),
                "by_role": profile.get("by_role"),
                "by_author": profile.get("by_author")
            })

        # Persist the generated upload_ids back to the audit file
        if needs_save:
            from monthly_file_audit import write_audit_history
            write_audit_history(history)

        uploads = sorted(
            uploads,
            key=lambda x: x.get("uploaded_at") or "",
            reverse=True
        )

        return uploads

    except Exception as e:
        return {
            "error": f"Erreur rÃ©cupÃ©ration historique uploads : {str(e)}"
        }

MONTHLY_DF_CACHE = {}

def load_monthly_file_cached(file_path: str):
    file_mtime = os.path.getmtime(file_path)
    cache_key = f"{file_path}:{file_mtime}"

    if cache_key in MONTHLY_DF_CACHE:
        print(f"[CACHE HIT] Loaded {file_path} from cache")
        return MONTHLY_DF_CACHE[cache_key]

    print(f"[CACHE MISS] Reading {file_path} from disk")
    df = load_monthly_jira_file(file_path)
    MONTHLY_DF_CACHE.clear()
    MONTHLY_DF_CACHE[cache_key] = df

    return df

@router.get("/pivot-by-upload")
def get_monthly_pivot_by_upload(
    upload_id: str,
    month: str,
    start_date: str = None,
    end_date: str = None,
    analysis_type: str = "all"
):
    try:
        history = read_audit_history()

        selected_upload = None

        for item in history:
            # Generate upload_id for legacy entries that don't have one
            existing_id = item.get("upload_id")
            if not existing_id:
                import hashlib
                raw = f"{item.get('uploaded_at', '')}_{item.get('original_filename', '')}"
                existing_id = hashlib.md5(raw.encode()).hexdigest()[:16]
                item["upload_id"] = existing_id

            if existing_id == upload_id:
                selected_upload = item
                break

        if not selected_upload:
            return {
                "error": f"Aucun fichier trouvÃ© pour upload_id={upload_id}"
            }

        archived_file_path = selected_upload.get("archived_file_path")

        # Docker compatibility fallback
        if archived_file_path and not os.path.exists(archived_file_path):
            filename = os.path.basename(archived_file_path.replace('\\', '/'))
            internal_path = os.path.join(str(MONTHLY_DATA_DIR), "imports", filename)
            if os.path.exists(internal_path):
                archived_file_path = internal_path

        if not archived_file_path or not os.path.exists(archived_file_path):
            return {
                "error": "Le fichier archivÃ© est introuvable."
            }

        df = load_monthly_file_cached(archived_file_path)

        base_response = {
            "month": month,
            "start_date": start_date,
            "end_date": end_date,
            "upload": {
                "upload_id": selected_upload.get("upload_id"),
                "original_filename": selected_upload.get("original_filename"),
                "uploaded_at": selected_upload.get("uploaded_at"),
                "profile": selected_upload.get("profile")
            },
            "source_file": archived_file_path,
            "source_rows_count": int(len(df))
        }

        if analysis_type == "daily":
            base_response["daily_summary"] = compute_daily_summary(
                df, month, start_date, end_date
            )
            return base_response

        if analysis_type == "role":
            base_response["by_role"] = compute_by_role(
                df, month, start_date, end_date
            )
            base_response["role_work_summary"] = compute_role_work_summary(
                df, month, start_date, end_date
            )
            return base_response

        if analysis_type == "author":
            base_response["by_author"] = compute_by_author(
                df, month, start_date, end_date
            )
            base_response["author_work_summary"] = compute_author_work_summary(
                df, month, start_date, end_date
            )
            return base_response

        # Default "all"
        pivot = compute_daily_role_pivot(df, month, start_date, end_date)
        by_role = compute_by_role(df, month, start_date, end_date)
        by_author = compute_by_author(df, month, start_date, end_date)
        by_project = compute_by_project(df, month, start_date, end_date)

        daily_summary = compute_daily_summary(df, month, start_date, end_date)
        role_work_summary = compute_role_work_summary(df, month, start_date, end_date)
        author_work_summary = compute_author_work_summary(df, month, start_date, end_date)

        group_classification = compute_group_classification(df, month, start_date, end_date)
        author_classification = compute_author_classification(df, month, start_date, end_date)

        base_response.update({
            "pivot_by_role_daily": pivot,
            "by_role": by_role,
            "by_author": by_author,
            "by_project": by_project,
            "daily_summary": daily_summary,
            "role_work_summary": role_work_summary,
            "author_work_summary": author_work_summary,
            "group_classification": group_classification,
            "author_classification": author_classification
        })

        return base_response

    except Exception as e:
        return {
            "error": f"Erreur gÃ©nÃ©ration pivot depuis fichier archivÃ© : {str(e)}"
        }

from fastapi.responses import StreamingResponse
import io
import pandas as pd
import datetime

@router.get("/download-report/{upload_id}")
def api_download_monthly_report(upload_id: str):
    try:
        history = read_audit_history()
        selected_upload = None

        for item in history:
            existing_id = item.get("upload_id")
            if not existing_id:
                import hashlib
                raw = f"{item.get('uploaded_at', '')}_{item.get('original_filename', '')}"
                existing_id = hashlib.md5(raw.encode()).hexdigest()[:16]
            if existing_id == upload_id:
                selected_upload = item
                break

        if not selected_upload:
            return {"error": f"Aucun fichier trouvé pour upload_id={upload_id}"}

        archived_file_path = selected_upload.get("archived_file_path")

        if archived_file_path and not os.path.exists(archived_file_path):
            filename = os.path.basename(archived_file_path.replace('\\', '/'))
            internal_path = os.path.join(str(MONTHLY_DATA_DIR), "imports", filename)
            if os.path.exists(internal_path):
                archived_file_path = internal_path

        if not archived_file_path or not os.path.exists(archived_file_path):
            return {"error": "Le fichier archivé est introuvable."}

        df = load_monthly_file_cached(archived_file_path)
        profile = selected_upload.get("profile", {})
        month = "Toutes dates"
        start_date = profile.get("min_date")
        end_date = profile.get("max_date")

        daily_summary = compute_daily_summary(df, month, start_date, end_date)
        role_work_summary = compute_role_work_summary(df, month, start_date, end_date)
        author_work_summary = compute_author_work_summary(df, month, start_date, end_date)

        # Convert summaries to DataFrames
        df_daily = pd.DataFrame(daily_summary) if daily_summary else pd.DataFrame()
        df_role = pd.DataFrame(role_work_summary) if role_work_summary else pd.DataFrame()
        df_author = pd.DataFrame(author_work_summary) if author_work_summary else pd.DataFrame()

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name="Données Jira", index=False)
            if not df_daily.empty:
                df_daily.to_excel(writer, sheet_name="Suivi Quotidien", index=False)
            if not df_role.empty:
                df_role.to_excel(writer, sheet_name="Résumé par Rôle", index=False)
            if not df_author.empty:
                df_author.to_excel(writer, sheet_name="Résumé par Auteur", index=False)

        output.seek(0)
        
        filename = f"Rapport_Analyse_{selected_upload.get('original_filename', 'Jira')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        return {"error": f"Erreur lors de la génération du rapport : {str(e)}"}


@router.get("/results")
def api_get_monthly_results():
    return get_monthly_results()

@router.get("/targets")
def api_get_monthly_targets():
    return get_monthly_targets()

@router.post("/target")
def api_save_monthly_target(request: TargetRequest):
    target = save_monthly_target(
        month=request.month,
        kpi_name=request.kpi_name,
        target_value=request.target_value,
        unit=request.unit,
        comparison=request.comparison,
        start_date=request.start_date,
        end_date=request.end_date
    )
    return {"message": "Target saved successfully", "target": target}

@router.post("/calculate")
def api_calculate_monthly(request: CalculateRequest):
    file_path = ACTIVE_MONTHLY_FILE
    if not os.path.exists(file_path):
        return {"error": "Aucun fichier de donnÃ©es actif trouvÃ©. Veuillez importer un fichier d'abord."}

    try:
        df = load_monthly_jira_file(file_path)
        
        if request.kpi_name == "monthly_total_hours":
            result_data = compute_monthly_total_hours(
                df,
                request.month,
                request.start_date,
                request.end_date
            )
        else:
            return {"error": f"KPI '{request.kpi_name}' non supportÃ© pour le moment."}
        
        saved_result = save_monthly_result(
            month=result_data["month"],
            kpi_name=result_data["kpi_name"],
            value=result_data["value"],
            unit=result_data["unit"],
            total_md=result_data.get("total_md")
        )
        
        target = find_target(request.month, request.kpi_name)
        comparison_result = None
        if target:
            comparison_result = compare_with_target(
                result_value=result_data["value"],
                target_value=target["target_value"],
                comparison=target["comparison"]
            )
            
        from monthly_file_audit import read_audit_history
        history = read_audit_history()
        history = sorted(history, key=lambda x: x.get("uploaded_at") or "", reverse=True)
        current_upload = history[0] if history else None
        
        if current_upload and not current_upload.get("upload_id"):
            import hashlib
            raw = f"{current_upload.get('uploaded_at', '')}_{current_upload.get('original_filename', '')}"
            current_upload["upload_id"] = hashlib.md5(raw.encode()).hexdigest()[:16]
            
        return {
            "message": "Calcul terminÃ© avec succÃ¨s",
            "result": saved_result,
            "comparison": comparison_result,
            "upload": current_upload
        }
        
    except Exception as e:
        return {"error": f"Erreur lors du calcul: {str(e)}"}

@router.get("/comparison")
def api_get_monthly_comparison(month: str = Query(...), kpi_name: str = Query("monthly_total_hours")):
    try:
        result = find_result(month, kpi_name)
        target = find_target(month, kpi_name)

        if not result:
            return {
                "error": f"Aucun rÃ©sultat trouvÃ© pour {month} / {kpi_name}"
            }

        if not target:
            return {
                "result": result,
                "target": None,
                "comparison": None,
                "message": "Aucune cible dÃ©finie pour ce mois."
            }

        comparison = compare_with_target(
            result_value=result["value"],
            target_value=target["target_value"],
            comparison=target["comparison"]
        )

        return {
            "result": result,
            "target": target,
            "comparison": comparison
        }

    except Exception as e:
        return {
            "error": f"Erreur comparaison mensuelle : {str(e)}"
        }
