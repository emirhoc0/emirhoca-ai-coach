from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from app.database import get_db
from sqlalchemy.orm import Session
from app.models import Program, AdjustmentEvent

router = APIRouter(prefix="/weekly-review", tags=["review"])

class WeeklyReviewIn(BaseModel):
    user_id: int
    train_completion_pct: float       # 0-100
    avg_rpe: float                    # e.g. 6-10
    avg_soreness: float               # 0-10
    sleep_hours: float                # avg last 7d
    weight_start: float               # kg, start of week
    weight_end: float                 # kg, end of week
    goal: str                         # "cut" | "bulk" | "recomp"
    steps_avg: int                    # last 7d avg
    calories: int                     # current daily calories (from last plan)

class WeeklyReviewOut(BaseModel):
    coach_note: str
    adjustment: Dict[str, Any]
    saved: bool
    created_at: datetime

# ---------- helpers ----------
def _load_latest_program(db: Session, user_id: int) -> Program:
    prog = (
        db.query(Program)
        .filter(Program.user_id == user_id)
        .order_by(Program.created_at.desc())
        .first()
    )
    return prog

def _mutate_sets(plan: dict, delta: int, max_targets: int = 2) -> List[str]:
    """
    Add or remove 1 set from up to `max_targets` main exercises across the first days.
    Returns list of exercise names changed.
    """
    changed = []
    if not plan or "days" not in plan:
        return changed

    count = 0
    for day in plan["days"]:
        if count >= max_targets:
            break
        workout = day.get("workout", [])
        if not workout:
            continue
        # treat first movement of the day as key lift
        ex = workout[0]
        sets_val = ex.get("sets", 3)
        new_sets = max(2, sets_val + delta)  # never below 2
        if new_sets != sets_val:
            ex["sets"] = new_sets
            changed.append(ex.get("exercise", f"day{day.get('day')}#0"))
            count += 1
    return changed

# ---------- endpoint ----------
@router.post("/", response_model=WeeklyReviewOut)
def weekly_review(payload: WeeklyReviewIn, db: Session = Depends(get_db)):
    # 1) Fetch current plan
    prog_row = _load_latest_program(db, payload.user_id)
    if not prog_row:
        raise HTTPException(status_code=404, detail="No program found for user. Generate a plan first.")

    try:
        plan = json.loads(prog_row.plan_json)
    except Exception:
        plan = {"days": []}

    notes: List[str] = []
    adjustments: Dict[str, Any] = {"training": "maintain", "nutrition": "maintain"}

    # 2) TRAINING rules
    # +1 set if train ≥85% & RPE <8  (ignoring PR check for MVP)
    key_lifts_changed: List[str] = []
    if payload.train_completion_pct >= 85 and payload.avg_rpe < 8:
        key_lifts_changed = _mutate_sets(plan, +1, max_targets=2)
        if key_lifts_changed:
            adjustments["training"] = f"+1 set on {', '.join(key_lifts_changed)}"
            notes.append("High adherence and manageable effort — adding 1 set to key lifts.")
        else:
            notes.append("Training looks good — no eligible lifts to increase.")
    # −1 set if RPE ≥9 or soreness ≥7/10
    elif payload.avg_rpe >= 9 or payload.avg_soreness >= 7:
        key_lifts_changed = _mutate_sets(plan, -1, max_targets=2)
        if key_lifts_changed:
            adjustments["training"] = f"-1 set on {', '.join(key_lifts_changed)}"
            notes.append("Fatigue high — reducing 1 set on key lifts for recovery.")
        else:
            notes.append("Fatigue high but no eligible lifts to reduce further.")
    else:
        notes.append("Training balance looks solid — no volume change.")

    # 3) NUTRITION rules
    weight_diff = payload.weight_end - payload.weight_start
    weight_pct = (weight_diff / payload.weight_start * 100.0) if payload.weight_start else 0.0

    kcal_change = 0
    steps_change = 0

    if payload.goal == "cut":
        if weight_pct > -0.25:  # loss slower than 0.25%/wk
            kcal_change = -150
            steps_change = +1000
            adjustments["nutrition"] = "-150 kcal or +1k steps"
            notes.append("Cut: weight loss <0.25%/wk — decrease 150 kcal or add 1k steps/day.")
        else:
            notes.append("Cut: rate of loss looks fine — keep calories.")
    elif payload.goal == "bulk":
        if weight_pct > 0.7:
            kcal_change = -100
            adjustments["nutrition"] = "-100 kcal"
            notes.append("Bulk: gaining >0.7%/wk — reduce 100 kcal.")
        elif weight_pct < 0.25:
            kcal_change = +100
            adjustments["nutrition"] = "+100 kcal"
            notes.append("Bulk: gaining <0.25%/wk — add 100 kcal.")
        else:
            notes.append("Bulk: gain rate on target — keep calories.")
    else:
        notes.append("Recomp: keep calories steady unless adherence issues.")

    # 4) Sleep note
    if payload.sleep_hours < 6.5:
        notes.append("Sleep <6.5h — prioritize 7–8h for recovery and performance.")

    # 5) Apply nutrition change to the plan metadata (non-breaking)
    plan.setdefault("nutrition", {})
    plan["nutrition"]["current_calories"] = payload.calories + kcal_change if kcal_change else payload.calories
    plan["nutrition"]["recommendation"] = adjustments["nutrition"]
    plan["last_reviewed_at"] = datetime.utcnow().isoformat()

    # 6) Save changes: update program + insert adjustment_event
    changes = {
        "training_changed_exercises": key_lifts_changed,
        "training_action": adjustments["training"],
        "nutrition_kcal_delta": kcal_change,
        "nutrition_steps_delta": steps_change,
        "weight_week_change_pct": round(weight_pct, 3),
        "inputs": payload.dict(),
        "note": " ; ".join(notes),
    }
    prog_row.plan_json = json.dumps(plan, ensure_ascii=False)
    db.add(prog_row)

    db.add(AdjustmentEvent(
        user_id=payload.user_id,
        payload_json=json.dumps(changes, ensure_ascii=False),
        reason="weekly_auto_adjust"
    ))
    db.commit()

    coach_note = " ".join(notes)
    return {
        "coach_note": coach_note,
        "adjustment": adjustments,
        "saved": True,
        "created_at": datetime.utcnow(),
    }
