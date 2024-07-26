from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship

from icecream import ic

# Database setup
DATABASE_URL = "sqlite:///./jobs.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Job and Company models
class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    contactEmail = Column(String)
    contactPhone = Column(String)

    jobs = relationship("Job", back_populates="company")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    type = Column(String)
    description = Column(String)
    location = Column(String)
    salary = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))

    company = relationship("Company", back_populates="jobs")

Base.metadata.create_all(bind=engine)

# Pydantic models
class CompanyModel(BaseModel):
    name: str
    description: str
    contactEmail: str
    contactPhone: str

class JobModel(BaseModel):
    id: Optional[int] = None
    title: str
    type: str
    description: str
    location: str
    salary: str
    company: CompanyModel

class JobResponse(JobModel):
    id: int

# FastAPI app
app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_company_data(company_id: int, db: Session):
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return {
        "name": company.name,
        "description": company.description,
        "contactEmail": company.contactEmail,
        "contactPhone": company.contactPhone
    }

# CRUD operations
@app.post("/jobs", response_model=JobResponse)
def create_job(job: JobModel, db: Session = Depends(get_db)):
    # Create company if it doesn't exist
    company = Company(**job.company.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)

    del job.company

    # Create job
    new_job = Job(**job.model_dump(), company_id=company.id)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


@app.get("/jobs", response_model=List[JobResponse])
def read_jobs(skip: int = 0, limit: int = 999, db: Session = Depends(get_db)):
    jobs = db.query(Job).offset(skip).limit(limit).all()
    return jobs

@app.get("/jobs/{job_id}", response_model=JobResponse)
def read_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.put("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job: JobModel, db: Session = Depends(get_db)):
    # Retrieve the existing job
    job_db = db.query(Job).filter(Job.id == job_id).one()
    
    # Update job attributes
    job_db.title = job.title
    job_db.type = job.type
    job_db.description = job.description
    job_db.location = job.location
    job_db.salary = job.salary

    # Retrieve the associated company
    company = job_db.company
    
    # Update company attributes
    company.name = job.company.name
    company.description = job.company.description
    company.contactEmail = job.company.contactEmail
    company.contactPhone = job.company.contactPhone

    # Commit the changes
    db.commit()
    db.refresh(job_db)
    
    return job_db

@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(db_job)
    db.commit()
    return {"detail": "Job deleted successfully"}
