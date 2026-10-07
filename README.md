# Bulk Certificate Generator

A FastAPI application for creating bulk certificate generation jobs, tracking generation progress, and downloading generated PDF certificates. The project includes a simple HTML/CSS/JavaScript frontend served by the same FastAPI app.

## Tech Stack

- Python
- FastAPI
- SQLite with SQLAlchemy
- ReportLab for PDF generation
- HTML, CSS, and vanilla JavaScript frontend
- Pytest for automated tests

## How To Set Up The Project

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The application uses SQLite and stores local data under the `data/` directory. The database and certificate folders are created automatically when the app starts.

## How To Run The Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

Open the frontend:

```text
http://127.0.0.1:8000/
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

The frontend lets you add recipients manually or paste CSV-style rows:

```text
Name, email, optional message
Asha Rao, asha@example.com, Great work
Dev Kumar, dev@example.com, Outstanding progress
```

## How To Run Tests

Run the test suite:

```bash
pytest
```

If Windows temp permissions cause an issue, run tests with a local temporary directory:

```bash
pytest --basetemp .pytest-temp
```

## How To Submit A Certificate Generation Request

Send a `POST` request to `/jobs` with job details and at least one recipient.

```bash
curl -X POST http://127.0.0.1:8000/jobs ^
  -H "Content-Type: application/json" ^
  -d "{\"course_name\":\"Backend Engineering\",\"issuer_name\":\"Acme Learning\",\"issue_date\":\"2026-10-07\",\"event_name\":\"October Cohort\",\"recipients\":[{\"name\":\"Asha Rao\",\"email\":\"asha@example.com\"},{\"name\":\"Dev Kumar\",\"email\":\"dev@example.com\",\"custom_message\":\"Great work\"}]}"
```

Example response:

```json
{
  "job_id": 1,
  "status": "pending",
  "total_count": 2
}
```

Check job progress with:

```bash
curl http://127.0.0.1:8000/jobs/1
```

The job status response includes:

- Overall job status
- Total certificate count
- Successful generation count
- Failure count
- Progress percentage
- Per-recipient certificate status

## How To Retrieve Generated Certificates

After a certificate has the `generated` status, download it with:

```bash
curl -o certificate.pdf http://127.0.0.1:8000/jobs/1/certificates/1
```

The download endpoint format is:

```text
GET /jobs/{job_id}/certificates/{certificate_id}
```

Only successfully generated certificates can be downloaded. Pending or failed certificates return `409 Conflict`. Missing certificates or missing files return `404 Not Found`.

## Important Implementation And Design Decisions

- FastAPI is used because it is lightweight, easy to run locally, supports automatic request validation, and provides built-in OpenAPI documentation.
- The frontend is served from FastAPI so the project runs as a single local application without requiring a separate frontend build system.
- SQLite is used so the app works locally without external database setup.
- SQLAlchemy models separate job-level data from recipient-level certificate records.
- Certificate generation runs as a FastAPI background task, allowing the create-job endpoint to respond quickly while PDFs are generated afterward.
- Each recipient is processed independently. If one certificate fails, the remaining certificates still continue.
- ReportLab is used to generate deterministic PDF certificates with a fixed template.
- Generated certificate files are stored under `data/certificates/{job_id}/`.
- Pydantic schemas validate incoming request data, including required fields and recipient email format.
- Tests use an isolated temporary SQLite database and temporary certificate output directory so test runs do not depend on production data.

## Failure Handling

Invalid request payloads fail with FastAPI validation errors before a job is created. During generation, each certificate is handled independently. A generation error marks only that recipient's certificate as failed and records the error message in the job status response.
