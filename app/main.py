from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from . import models
from .routers import health

app = FastAPI(title=settings.app_name)

# Auto-create tables (Phase 2 deliverable)
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"msg": "Emirali AI Coach API is up."}

# Health/router
app.include_router(health.router)
from app.routers import plan
app.include_router(plan.router)


from .routers import plan as plan_router
app.include_router(plan_router.router)

from app.routers import review
app.include_router(review.router)


# Example user bootstrap endpoint (simple demo)
from fastapi import APIRouter
from .schemas import UserCreate, UserOut
from .models import User

api = APIRouter(prefix="/users", tags=["users"])

@api.post("/", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    u = User(email=payload.email, name=payload.name)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

app.include_router(api)