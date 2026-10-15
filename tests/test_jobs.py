def test_create_and_get_job(client, auth_headers, sample_job):
    r = client.post("/jobs", json=sample_job, headers=auth_headers)
    assert r.status_code == 201
    body = r.json()
    job_id = body["id"]
    assert body["technologies"] == ["Python", "FastAPI", "PyTorch"]
    assert body["status"] == "saved"
    r = client.get(f"/jobs/{job_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "Junior AI Engineer"


def test_list_jobs_pagination(client, auth_headers, sample_job):
    for i in range(3):
        sample_job["title"] = f"Job {i}"
        client.post("/jobs", json=sample_job, headers=auth_headers)
    r = client.get("/jobs?page=1&limit=2", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["limit"] == 2
    assert len(body["items"]) == 2


def test_filter_jobs_by_status(client, auth_headers, sample_job):
    sample_job["status"] = "applied"
    client.post("/jobs", json=sample_job, headers=auth_headers)
    sample_job["status"] = "saved"
    client.post("/jobs", json=sample_job, headers=auth_headers)
    r = client.get("/jobs?status=applied", headers=auth_headers)
    assert r.json()["total"] == 1


def test_filter_jobs_by_location(client, auth_headers, sample_job):
    sample_job["location"] = "Remote"
    client.post("/jobs", json=sample_job, headers=auth_headers)
    sample_job["location"] = "Boston"
    client.post("/jobs", json=sample_job, headers=auth_headers)
    r = client.get("/jobs?location=remote", headers=auth_headers)
    assert r.json()["total"] == 1


def test_filter_jobs_by_technology(client, auth_headers, sample_job):
    sample_job["technologies"] = ["Python", "PyTorch"]
    client.post("/jobs", json=sample_job, headers=auth_headers)
    sample_job["technologies"] = ["JavaScript"]
    client.post("/jobs", json=sample_job, headers=auth_headers)
    r = client.get("/jobs?technology=PyTorch", headers=auth_headers)
    assert r.json()["total"] == 1


def test_search_jobs(client, auth_headers, sample_job):
    client.post("/jobs", json=sample_job, headers=auth_headers)
    r = client.get("/jobs?search=Junior", headers=auth_headers)
    assert r.json()["total"] == 1


def test_update_job_status(client, auth_headers, sample_job):
    job_id = client.post("/jobs", json=sample_job, headers=auth_headers).json()["id"]
    r = client.patch(f"/jobs/{job_id}", json={"status": "interview"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "interview"


def test_update_job_multiple_fields(client, auth_headers, sample_job):
    job_id = client.post("/jobs", json=sample_job, headers=auth_headers).json()["id"]
    r = client.patch(f"/jobs/{job_id}", json={"status": "offer", "location": "NYC", "technologies": ["Python"]}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "offer"
    assert body["location"] == "NYC"
    assert body["technologies"] == ["Python"]


def test_invalid_status_rejected(client, auth_headers, sample_job):
    job_id = client.post("/jobs", json=sample_job, headers=auth_headers).json()["id"]
    r = client.patch(f"/jobs/{job_id}", json={"status": "banana"}, headers=auth_headers)
    assert r.status_code == 422


def test_get_nonexistent_job_returns_404(client, auth_headers):
    r = client.get("/jobs/9999", headers=auth_headers)
    assert r.status_code == 404


def test_delete_job(client, auth_headers, sample_job):
    job_id = client.post("/jobs", json=sample_job, headers=auth_headers).json()["id"]
    r = client.delete(f"/jobs/{job_id}", headers=auth_headers)
    assert r.status_code == 204
    assert client.get(f"/jobs/{job_id}", headers=auth_headers).status_code == 404


def test_user_cannot_read_other_users_job(client, auth_headers, second_user_headers, sample_job):
    job_id = client.post("/jobs", json=sample_job, headers=auth_headers).json()["id"]
    r = client.get(f"/jobs/{job_id}", headers=second_user_headers)
    assert r.status_code == 404


def test_user_cannot_update_other_users_job(client, auth_headers, second_user_headers, sample_job):
    job_id = client.post("/jobs", json=sample_job, headers=auth_headers).json()["id"]
    r = client.patch(f"/jobs/{job_id}", json={"status": "offer"}, headers=second_user_headers)
    assert r.status_code == 404


def test_user_cannot_delete_other_users_job(client, auth_headers, second_user_headers, sample_job):
    job_id = client.post("/jobs", json=sample_job, headers=auth_headers).json()["id"]
    r = client.delete(f"/jobs/{job_id}", headers=second_user_headers)
    assert r.status_code == 404


def test_users_see_only_their_own_jobs(client, auth_headers, second_user_headers, sample_job):
    client.post("/jobs", json=sample_job, headers=auth_headers)
    client.post("/jobs", json=sample_job, headers=auth_headers)
    client.post("/jobs", json=sample_job, headers=second_user_headers)
    a = client.get("/jobs", headers=auth_headers).json()
    b = client.get("/jobs", headers=second_user_headers).json()
    assert a["total"] == 2
    assert b["total"] == 1
