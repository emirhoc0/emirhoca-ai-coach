from fastapi import APIRouter
from app.schemas import PlanGenerateIn, PlanGenerateOut
from app.services.planner import build_program
from app.services.nutrition import macros, meal_templates

router = APIRouter(prefix="/plan", tags=["plan"])

@router.post("/generate", response_model=PlanGenerateOut)
def generate_plan(payload: PlanGenerateIn):
    prog = build_program(payload.days_per_week, payload.equipment, payload.injuries)
    m = macros(payload.goal, payload.sex, payload.age, payload.height_cm, payload.weight_kg, payload.days_per_week)
    return {**prog, **m, "meals": meal_templates(m["calories"])}