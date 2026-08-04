from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user
from app.schemas import DashboardStats
from app.services import dashboard_service

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def stats(user: current_user, db: Session = Depends(get_db)):
    return dashboard_service.get_stats(db, user)
