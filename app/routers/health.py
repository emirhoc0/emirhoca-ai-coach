from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..deps import db_dep

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/ping")
def ping(db: Session = Depends(db_dep)):
    # quick DB check by opening/closing a connection
    db.execute("SELECT 1")
    return {"ok": True, "service": "emirhoca-ai-coach"}