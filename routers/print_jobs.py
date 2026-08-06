from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db
from routers.auth import require_admin

# File d'impression : seul le central (loopback = admin) la consomme.
router = APIRouter(prefix="/print-jobs", tags=["PrintJobs"],
                   dependencies=[Depends(require_admin)])


@router.get("/", response_model=List[schemas.PrintJobRead])
def list_jobs(status_filter: str = "pending", db: Session = Depends(get_db)):
    query = db.query(models.PrintJob)
    if status_filter:
        query = query.filter(models.PrintJob.status == status_filter)
    return query.order_by(models.PrintJob.created_at).all()


@router.post("/{job_id}/done", response_model=schemas.PrintJobRead)
def mark_done(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.PrintJob).filter(models.PrintJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found.")
    job.status = "done"
    job.printed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job
