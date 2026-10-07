from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db, init_db
from app.models import CertificateRecord, CertificateStatus
from app.schemas import CertificateJobCreate, CertificateJobCreated, CertificateJobStatus
from app.services import build_job_status, create_job, process_job


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Bulk Certificate Generator API", lifespan=lifespan)

STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.post("/jobs", response_model=CertificateJobCreated, status_code=201)
def create_certificate_job(
    payload: CertificateJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> CertificateJobCreated:
    job = create_job(db, payload)
    background_tasks.add_task(process_job, job.id, SessionLocal)
    return CertificateJobCreated(job_id=job.id, status=job.status, total_count=job.total_count)


@app.get("/jobs/{job_id}", response_model=CertificateJobStatus)
def get_certificate_job(job_id: int, db: Session = Depends(get_db)) -> dict:
    job = create_job_query(db, job_id)
    return build_job_status(job)


@app.get("/jobs/{job_id}/certificates/{certificate_id}")
def download_certificate(job_id: int, certificate_id: int, db: Session = Depends(get_db)) -> FileResponse:
    certificate = (
        db.query(CertificateRecord)
        .filter(CertificateRecord.job_id == job_id, CertificateRecord.id == certificate_id)
        .first()
    )
    if certificate is None:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if certificate.status != CertificateStatus.generated or not certificate.file_path:
        raise HTTPException(status_code=409, detail="Certificate is not available")

    file_path = Path(certificate.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Certificate file is missing")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=file_path.name,
    )


def create_job_query(db: Session, job_id: int):
    from app.models import CertificateJob

    job = db.get(CertificateJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
