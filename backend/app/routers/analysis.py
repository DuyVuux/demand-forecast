from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials

from ..services.analysis_service import (
    column_detail,
    get_cached_result_by_job,
    job_status,
    prepare_job,
    register_job,
    run_job,
    compute_filters_for_job,
    compute_overview_for_job,
    get_runtime_config,
    update_runtime_config,
    export_config_json,
    import_config_json,
)
from ..models.schemas import AnalysisConfigUpdate
from ..utils.auth import require_roles, bearer_scheme, decode_token
from ..utils.logger import get_logger

router = APIRouter(prefix="/analysis", tags=["analysis"])
log = get_logger("router.analysis")


@router.post("/upload")
async def upload_data(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Nhận file raw (CSV/Excel/Parquet), tạo job phân tích async và trả về job_id."""
    username = "anonymous"
    if creds and getattr(creds, "credentials", None):
        try:
            payload = decode_token(creds.credentials)
            username = payload.get("sub", "unknown")
        except Exception:
            username = "invalid_token"

    log.info("user=%s attempting to upload filename=%s", username, file.filename)
    try:
        content = await file.read()
        log.info("File %s read into memory, size=%d bytes", file.filename, len(content))

        job_id, file_hash, path = prepare_job(content, file.filename)
        log.info("Job prepared for %s. job_id=%s, path=%s", file.filename, job_id, path)

        register_job(job_id, file_hash, str(path), file.filename)
        log.info("Job %s registered.", job_id)

        background.add_task(run_job, job_id)
        log.info("Background task for job_id=%s scheduled.", job_id)

        return {
            "status": "success",
            "message": "File uploaded successfully and analysis started.",
            "job_id": job_id,
            "filename": file.filename,
        }
    except Exception as e:
        log.exception("Upload failed for user=%s, filename=%s. Error: %s", username, file.filename, e)
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Could not process file: {e}"},
        )


@router.get("/status/{job_id}")
async def status(job_id: str):
    return job_status(job_id)


@router.get("/summary")
async def summary(job_id: str = Query(...)):
    st = job_status(job_id)
    if st.get("status") != "finished":
        return JSONResponse(status_code=202, content={"detail": "processing", "status": st.get("status"), "job": st})
    # Recompute dynamically based on current config to reflect user overrides
    try:
        return compute_overview_for_job(job_id)
    except FileNotFoundError:
        # Fallback: return cached overview if file missing
        data = get_cached_result_by_job(job_id)
        if not data:
            raise HTTPException(status_code=404, detail="Kết quả chưa sẵn sàng")
        return data["overview"]


@router.get("/quality")
async def quality(job_id: str = Query(...)):
    st = job_status(job_id)
    if st.get("status") != "finished":
        return JSONResponse(status_code=202, content={"detail": "processing", "status": st.get("status"), "job": st})
    data = get_cached_result_by_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Kết quả chưa sẵn sàng")
    return data["quality"]


@router.get("/insights")
async def insights(job_id: str = Query(...)):
    st = job_status(job_id)
    if st.get("status") != "finished":
        return JSONResponse(status_code=202, content={"detail": "processing", "status": st.get("status"), "job": st})
    data = get_cached_result_by_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Kết quả chưa sẵn sàng")
    return data["insights"]


@router.get("/correlation")
async def correlation(job_id: str = Query(...)):
    st = job_status(job_id)
    if st.get("status") != "finished":
        return JSONResponse(status_code=202, content={"detail": "processing", "status": st.get("status"), "job": st})
    data = get_cached_result_by_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Kết quả chưa sẵn sàng")
    return data["correlation"]


@router.get("/columns/{name}")
async def column(name: str, job_id: str = Query(...), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    st = job_status(job_id)
    if st.get("status") != "finished":
        return JSONResponse(status_code=202, content={"detail": "processing", "status": st.get("status"), "job": st})
    try:
        return column_detail(job_id, name, page=page, page_size=page_size)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/columns/{name}/export")
async def export_column_csv(name: str, job_id: str = Query(...)):
    import io
    from ..services.analysis_service import export_column_detail_csv

    st = job_status(job_id)
    if st.get("status") != "finished":
        return JSONResponse(status_code=202, content={"detail": "processing", "status": st.get("status"), "job": st})
    
    try:
        csv_buffer = export_column_detail_csv(job_id, name)
        headers = {"Content-Disposition": f"attachment; filename=details_{name}_{job_id}.csv"}
        return StreamingResponse(csv_buffer, media_type="text/csv", headers=headers)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.exception(f"Failed to export column {name} for job {job_id}")
        raise HTTPException(status_code=500, detail=f"Could not export data: {e}")


@router.get("/result")
async def full_result(job_id: str = Query(...)):
    st = job_status(job_id)
    if st.get("status") != "finished":
        return JSONResponse(status_code=202, content={"detail": "processing", "status": st.get("status"), "job": st})
    data = get_cached_result_by_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Kết quả chưa sẵn sàng")
    return data


@router.get("/export/json")
async def export_json(job_id: str = Query(...)):
    data = get_cached_result_by_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Không có dữ liệu")
    return JSONResponse(content=data, media_type="application/json")


@router.get("/export/csv")
async def export_csv(job_id: str = Query(...)):
    import io
    import csv

    data = get_cached_result_by_job(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Không có dữ liệu")

    # Xuất phần overview.columns thành CSV
    cols = data.get("overview", {}).get("columns", [])
    if not cols:
        raise HTTPException(status_code=400, detail="Không có dữ liệu cột để xuất")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["name", "dtype", "null_pct", "unique_pct", "min", "max", "mean", "median"])
    writer.writeheader()
    for item in cols:
        writer.writerow({
            "name": item.get("name"),
            "dtype": item.get("dtype"),
            "null_pct": item.get("null_pct"),
            "unique_pct": item.get("unique_pct"),
            "min": item.get("min"),
            "max": item.get("max"),
            "mean": item.get("mean"),
            "median": item.get("median"),
        })

    output.seek(0)
    headers = {"Content-Disposition": f"attachment; filename=overview_{job_id}.csv"}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)


@router.get("/config")
async def get_config(
    job_id: Optional[str] = Query(None),
):
    cfg = get_runtime_config()
    if job_id:
        st = job_status(job_id)
        if st.get("status") != "finished":
            return JSONResponse(status_code=202, content={"detail": "processing", "status": st.get("status"), "job": st})
        filters = compute_filters_for_job(job_id)
        return {"config": cfg, "filters": filters}
    return {"config": cfg}


@router.post("/config")
async def post_config(
    payload: AnalysisConfigUpdate,
    user: Dict[str, Any] = Depends(require_roles({"analyst", "admin"})),
):
    saved = update_runtime_config(payload.dict(exclude_none=True))
    log.info("user=%s updated analysis config", user["username"])
    return {"config": saved}


@router.get("/config/export")
async def export_config():
    return export_config_json()


@router.post("/config/import")
async def import_config(
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles({"analyst", "admin"})),
):
    saved = import_config_json(payload)
    log.info("user=%s imported analysis config", user["username"])
    return {"config": saved}
