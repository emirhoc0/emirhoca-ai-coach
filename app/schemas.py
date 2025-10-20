from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict

# ---- Users (Phase 1–2) ----
class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: str
    class Config:
        from_attributes = True

# ---- Plan Generation (Phase 3) ----
class PlanGenerateIn(BaseModel):
    user_id: Optional[int] = None
    goal: str              # cut / bulk / recomp
    sex: str
    age: int
    height_cm: float
    weight_kg: float
    days_per_week: int
    session_minutes: int
    experience: str
    equipment: List[str] = []
    injuries: List[str] = []

class PlanGenerateOut(BaseModel):
    split: str
    days: List[Dict[str, Any]]
    key_lifts: List[str]
    progression_model: Dict[str, Any]
    why_split: str
    why_substitution: str
    calories: int
    protein_g: int
    fat_g: int
    carb_g: int
    tdee: int
    meals: List[Dict[str, Any]]