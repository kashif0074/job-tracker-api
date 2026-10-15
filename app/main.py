from fastapi import FastAPI

from app.routers import auth, jobs


app = FastAPI(title="AI Engineer Job Tracker API", version="1.0.0")

app.include_router(auth.router)
app.include_router(jobs.router)


@app.get("/")
def read_root():
    return {"message": "Job Tracker API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}