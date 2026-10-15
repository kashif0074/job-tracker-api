from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=True)

# Login as Alice
r = client.post(
    "/auth/login",
    data={"username": "alice@example.com", "password": "password123"},
)
print("LOGIN status:", r.status_code)
print("LOGIN body:", r.text[:200])

token = r.json()["access_token"]

# Hit /jobs
r = client.get("/jobs", headers={"Authorization": f"Bearer {token}"})
print("JOBS status:", r.status_code)
print("JOBS body:", r.text[:500])