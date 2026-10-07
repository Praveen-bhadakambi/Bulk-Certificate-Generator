from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import CertificateStatus, JobStatus


class RecipientCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    email: EmailStr
    custom_message: Annotated[str | None, Field(max_length=500)] = None


class CertificateJobCreate(BaseModel):
    course_name: Annotated[str, Field(min_length=1, max_length=200)]
    issuer_name: Annotated[str, Field(min_length=1, max_length=200)]
    issue_date: date
    event_name: Annotated[str | None, Field(max_length=200)] = None
    recipients: Annotated[list[RecipientCreate], Field(min_length=1, max_length=1000)]


class CertificateItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_name: str
    recipient_email: str
    status: CertificateStatus
    error_message: str | None = None


class CertificateJobCreated(BaseModel):
    job_id: int
    status: JobStatus
    total_count: int


class CertificateJobStatus(BaseModel):
    job_id: int
    status: JobStatus
    total_count: int
    success_count: int
    failure_count: int
    progress_percent: float
    certificates: list[CertificateItem]
