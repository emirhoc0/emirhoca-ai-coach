from __future__ import annotations
from typing import List, Dict, Any
import json, os

# Load exercise pool once
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exercises.json")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    EX_POOL = json.load(f)["exercises"]

SPLIT_RULES = {2: "UL", 3: "PPL", 4: "ULx2", 5: "PPL+UL", 6: "PPLx2"}

DOUBLE_PROGRESSION = {
    "sets": 3,
    "reps_min": 6,
    "reps_max": 10,
    "rir": "1-2",
    "note": "Double progression: 3x6–10 @ RIR 1–2; when all sets hit 10, add 2.5–5kg next time."
}

KEY_LIFTS = {
    "UL": ["Barbell Bench Press", "Barbell Back Squat"],
    "ULx2": ["Barbell Bench Press", "Barbell Back Squat"],
    "PPL": ["Barbell Bench Press", "Romanian Deadlift"],
    "PPL+UL": ["Barbell Bench Press", "Romanian Deadlift"],
    "PPLx2": ["Barbell Bench Press", "Romanian Deadlift"],
}

def filter_exercises(user_equipment: List[str], injuries: List[str]) -> List[Dict[str, Any]]:
    def ok(ex):
        equip_ok = (not user_equipment) or any(e in user_equipment for e in ex.get("equipment", []))
        inj_ok = not any(tag in injuries for tag in ex.get("injury_exclude", []))
        return equip_ok and inj_ok
    return [e for e in EX_POOL if ok(e)]

def pick(ex_pool: List[Dict[str, Any]], muscle: str) -> str:
    for e in ex_pool:
        if e["muscle"] == muscle:
            return e["name"]
    return ex_pool[0]["name"] if ex_pool else "Bodyweight Squat"

def make_day(ex_pool, focus: str) -> List[Dict[str, Any]]:
    if focus == "Upper":
        muscles = ["chest", "mid_back", "delts", "lats", "triceps", "biceps"]
    elif focus == "Lower":
        muscles = ["quads", "hamstrings", "glutes", "calves", "core"]
    elif focus == "Push":
        muscles = ["chest", "delts", "triceps", "chest"]
    elif focus == "Pull":
        muscles = ["lats", "mid_back", "biceps", "mid_back"]
    else:  # Legs
        muscles = ["quads", "hamstrings", "glutes", "calves", "core"]

    day = []
    for m in muscles:
        ex_name = pick(ex_pool, m)
        day.append({
            "exercise": ex_name,
            "sets": DOUBLE_PROGRESSION["sets"],
            "reps": f"{DOUBLE_PROGRESSION['reps_min']}-{DOUBLE_PROGRESSION['reps_max']}",
            "RIR": DOUBLE_PROGRESSION["rir"],
            "progression": DOUBLE_PROGRESSION["note"],
        })
    return day

def build_program(days_per_week: int, equipment: List[str], injuries: List[str]) -> Dict[str, Any]:
    split = SPLIT_RULES.get(days_per_week, "PPL")
    ex_pool = filter_exercises(equipment, injuries)

    if split == "UL":
        schedule = [{"day": 1, "focus": "Upper"}, {"day": 2, "focus": "Lower"}]
    elif split == "ULx2":
        schedule = [{"day": 1, "focus": "Upper"}, {"day": 2, "focus": "Lower"},
                    {"day": 3, "focus": "Upper"}, {"day": 4, "focus": "Lower"}]
    elif split == "PPL":
        schedule = [{"day": 1, "focus": "Push"}, {"day": 2, "focus": "Pull"}, {"day": 3, "focus": "Legs"}]
    elif split == "PPL+UL":
        schedule = [{"day": 1, "focus": "Push"}, {"day": 2, "focus": "Pull"}, {"day": 3, "focus": "Legs"},
                    {"day": 4, "focus": "Upper"}, {"day": 5, "focus": "Lower"}]
    else:  # PPLx2
        schedule = [{"day": 1, "focus": "Push"}, {"day": 2, "focus": "Pull"}, {"day": 3, "focus": "Legs"},
                    {"day": 4, "focus": "Push"}, {"day": 5, "focus": "Pull"}, {"day": 6, "focus": "Legs"}]

    days = [{"day": s["day"], "focus": s["focus"], "workout": make_day(ex_pool, s["focus"])} for s in schedule]

    return {
        "split": split,
        "days": days,
        "key_lifts": KEY_LIFTS.get(split, []),
        "why_split": "2→UL, 3→PPL, 4→ULx2, 5–6→PPL varyasyonları; toparlanma/volüm dengesine göre ölçeklenir.",
        "why_substitution": "Ekipman/yaralanma filtreleri ile güvenli alternatifler seçildi (örn. omuz sorunu → DB/Machine press).",
        "progression_model": DOUBLE_PROGRESSION,
    }
