from sqlalchemy.orm import Session

from app.certificate_generator import generate_certificate_pdf
from app.models import CertificateJob, CertificateRecord, CertificateStatus, JobStatus
from app.schemas import CertificateJobCreate


def create_job(db: Session, payload: CertificateJobCreate) -> CertificateJob:
    job = CertificateJob(
        course_name=payload.course_name,
        event_name=payload.event_name,
        issuer_name=payload.issuer_name,
        issue_date=payload.issue_date.isoformat(),
        total_count=len(payload.recipients),
    )
    db.add(job)
    db.flush()

    for recipient in payload.recipients:
        db.add(
            CertificateRecord(
                job_id=job.id,
                recipient_name=recipient.name,
                recipient_email=str(recipient.email),
                custom_message=recipient.custom_message,
            )
        )

    db.commit()
    db.refresh(job)
    return job


def process_job(job_id: int, session_factory) -> None:
    db: Session = session_factory()
    try:
        job = db.get(CertificateJob, job_id)
        if job is None:
            return

        job.status = JobStatus.processing
        db.commit()

        for certificate in job.certificates:
            try:
                output_path = generate_certificate_pdf(
                    job_id=job.id,
                    certificate_id=certificate.id,
                    recipient_name=certificate.recipient_name,
                    course_name=job.course_name,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date,
                    event_name=job.event_name,
                    custom_message=certificate.custom_message,
                )
                certificate.status = CertificateStatus.generated
                certificate.file_path = str(output_path)
                certificate.error_message = None
            except Exception as exc:
                certificate.status = CertificateStatus.failed
                certificate.error_message = str(exc)
            finally:
                db.add(certificate)
                db.commit()

        job.success_count = sum(1 for item in job.certificates if item.status == CertificateStatus.generated)
        job.failure_count = sum(1 for item in job.certificates if item.status == CertificateStatus.failed)
        if job.success_count and job.failure_count:
            job.status = JobStatus.completed_with_errors
        elif job.failure_count == job.total_count:
            job.status = JobStatus.failed
        else:
            job.status = JobStatus.completed
        db.add(job)
        db.commit()
    finally:
        db.close()


def build_job_status(job: CertificateJob) -> dict:
    processed = job.success_count + job.failure_count
    progress = round((processed / job.total_count) * 100, 2) if job.total_count else 0.0
    return {
        "job_id": job.id,
        "status": job.status,
        "total_count": job.total_count,
        "success_count": job.success_count,
        "failure_count": job.failure_count,
        "progress_percent": progress,
        "certificates": job.certificates,
    }
