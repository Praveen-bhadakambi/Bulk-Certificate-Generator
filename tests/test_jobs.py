def valid_payload():
    return {
        "course_name": "Backend Engineering",
        "issuer_name": "Acme Learning",
        "issue_date": "2026-10-07",
        "event_name": "October Cohort",
        "recipients": [
            {"name": "Asha Rao", "email": "asha@example.com"},
            {"name": "Dev Kumar", "email": "dev@example.com", "custom_message": "Great work"},
        ],
    }


def test_create_generation_job(client):
    response = client.post("/jobs", json=valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["job_id"] == 1
    assert body["total_count"] == 2
    assert body["status"] == "pending"


def test_input_validation_rejects_bad_recipient(client):
    payload = valid_payload()
    payload["recipients"][0]["email"] = "not-an-email"

    response = client.post("/jobs", json=payload)

    assert response.status_code == 422


def test_certificate_generation_and_job_progress(client):
    created = client.post("/jobs", json=valid_payload()).json()

    response = client.get(f"/jobs/{created['job_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["success_count"] == 2
    assert body["failure_count"] == 0
    assert body["progress_percent"] == 100.0
    assert all(item["status"] == "generated" for item in body["certificates"])


def test_individual_certificate_failure_does_not_stop_job(client):
    payload = valid_payload()
    payload["recipients"].append({"name": "fail generation", "email": "fail@example.com"})

    created = client.post("/jobs", json=payload).json()
    response = client.get(f"/jobs/{created['job_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed_with_errors"
    assert body["success_count"] == 2
    assert body["failure_count"] == 1
    failed = [item for item in body["certificates"] if item["status"] == "failed"]
    assert failed[0]["error_message"] == "Simulated certificate generation failure"


def test_retrieve_generated_certificate(client):
    created = client.post("/jobs", json=valid_payload()).json()
    job = client.get(f"/jobs/{created['job_id']}").json()
    certificate_id = job["certificates"][0]["id"]

    response = client.get(f"/jobs/{created['job_id']}/certificates/{certificate_id}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_unavailable_failed_certificate_returns_conflict(client):
    payload = valid_payload()
    payload["recipients"] = [{"name": "fail generation", "email": "fail@example.com"}]
    created = client.post("/jobs", json=payload).json()
    job = client.get(f"/jobs/{created['job_id']}").json()
    certificate_id = job["certificates"][0]["id"]

    response = client.get(f"/jobs/{created['job_id']}/certificates/{certificate_id}")

    assert response.status_code == 409
