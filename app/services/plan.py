from __future__ import annotations
from typing import Dict, Any, List, Tuple
import json, math, random
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "exercises.json"

def _load_exercises() -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

EXS = _load_exercises()

def filter_exercises(available_equip: List[str], injuries: List[str], muscle: str | None = None, tag: str | None = None) -> List[Dict[str, Any]]:
    eq = set([e.strip().lower() for e in available_equip or []])
    inj = set([i.strip().lower() for i in injuries or []])
    res = []
    for ex in EXS:
        if muscle and ex["muscle"] != muscle:
            continue
        if tag and tag not in ex["tags"]:
            continue
        # equipment intersection check (if no equip specified, allow bodyweight)
        if ex["equip"] and eq and not (eq & set(ex["equip"])):
            continue
        # injury filter
        if inj & set([a.lower() for a in ex.get("avoid_injuries", [])]):
            continue
        res.append(ex)
    return res

def choose_split(days_per_week: int) -> Tuple[str, List[str]]:
    if days_per_week <= 2:
        return "UL", ["Upper", "Lower"]
    if days_per_week == 3:
        return "PPL", ["Push", "Pull", "Legs"]
    if days_per_week == 4:
        return "UpperLower", ["Upper A", "Lower A", "Upper B", "Lower B"]
    # 5–6 → PPLx2 (repeat)
    return "PPLx2", ["Push A", "Pull A", "Legs A", "Push B", "Pull B", "Legs B"][:days_per_week]

def double_progression_block(name: str, muscle_targets: List[str], available_equip: List[str], injuries: List[str]) -> List[Dict[str, Any]]:
    # deterministic selection with fallback
    random.seed(name)  # stable per day label
    day_plan = []
    # priority: 1 comp per main muscle + 1-2 isolations
    for m in muscle_targets:
        pool = filter_exercises(available_equip, injuries, muscle=m, tag=None)
        # prefer compounds first
        compounds = [p for p in pool if "compound" in p["tags"]]
        isolations = [p for p in pool if "isolation" in p["tags"]]
        chosen = (compounds[:1] or pool[:1]) + isolations[:1]
        for ex in chosen:
            day_plan.append({
                "exercise": ex["name"],
                "sets": 3,
                "rep_range": "6-10",
                "rir": "1-2",
                "progression": "Double progression: add reps within 6–10; when all sets hit 10 reps, add 2.5–5 kg next time."
            })
    # add accessories if day is short
    if len(day_plan) < 5:
        # add any safe accessory
        extra = filter_exercises(available_equip, injuries)
        extras = []
        for ex in extra:
            if ex["name"] not in [d["exercise"] for d in day_plan] and len(extras) < 2:
                extras.append({
                    "exercise": ex["name"],
                    "sets": 2,
                    "rep_range": "10-15",
                    "rir": "1-2",
                    "progression": "Add reps within range; then +2.5 kg."
                })
        day_plan.extend(extras)
    return day_plan

def build_program(days_per_week: int, equipment: List[str], injuries: List[str]) -> Dict[str, Any]:
    split_key, day_labels = choose_split(days_per_week)
    plan = {"split": split_key, "days": []}

    # day templates by split
    templates = {
        "Upper": ["chest","back","shoulders","triceps","biceps"],
        "Lower": ["quads","hamstrings","glutes","calves"],
        "Push": ["chest","shoulders","triceps"],
        "Pull": ["back","rear_delts","biceps"],
        "Legs": ["quads","hamstrings","glutes","calves"],
    }

    for label in day_labels:
        key = label.split()[0]  # e.g., "Upper", "Lower", "Push"
        muscles = templates.get(key, ["chest","back","shoulders","quads"])
        plan["days"].append({
            "name": label,
            "work": double_progression_block(label, muscles, equipment, injuries)
        })

    why_split = {
        "UL": "2 days → Upper/Lower gives full-body frequency 2×/wk with enough volume per session.",
        "PPL": "3 days → Push/Pull/Legs hits each main pattern once per week with balanced fatigue.",
        "UpperLower": "4 days → Upper/Lower A/B increases frequency to ~2×/wk for faster progress.",
        "PPLx2": "5–6 days → PPL twice weekly supports advanced lifters with higher volume."
    }.get(plan["split"], "Selected split matches your available days for optimal frequency and recovery.")

    # simple substitution reason
    why_sub = "Exercises are filtered by your available equipment and known injuries to keep stimulus high while reducing risk."

    return {"program": plan, "why_split": why_split, "why_substitution": why_sub}

# --------- Nutrition ---------

def mifflin(height_cm: float, weight_kg: float, age: int, sex: str) -> float:
    s = 5 if sex.lower().startswith("m") else -161
    return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + s

def activity_multiplier(days_per_week: int, session_minutes: int) -> float:
    # simple deterministic mapping
    weekly_minutes = (days_per_week or 0) * (session_minutes or 0)
    if weekly_minutes < 60: return 1.2
    if weekly_minutes < 180: return 1.35
    if weekly_minutes < 300: return 1.5
    if weekly_minutes < 450: return 1.6
    return 1.75

def adjust_goal(cal: float, goal: str) -> float:
    g = (goal or "").lower()
    if g in ["cut","fatloss","lose","loss"]: return cal * 0.85
    if g in ["bulk","gain","mass"]: return cal * 1.08
    return cal  # maintain

def macros_from_goals(weight_kg: float, goal: str) -> Dict[str, int]:
    # Protein 1.8–2.2 g/kg → pick 2.0 g/kg; Fat 0.6–0.9 g/kg → pick 0.8 g/kg
    p = max(1.8, min(2.2, 2.0)) * weight_kg
    f = max(0.6, min(0.9, 0.8)) * weight_kg
    return {"protein_g": int(round(p)), "fat_g": int(round(f))}

def carbs_from_rest(calories: int, protein_g: int, fat_g: int) -> int:
    cal_from_p = protein_g * 4
    cal_from_f = fat_g * 9
    carb_cal = max(0, calories - cal_from_p - cal_from_f)
    return int(round(carb_cal / 4))

def meal_templates_tr(protein_g: int, carbs_g: int, fat_g: int) -> List[Dict[str, Any]]:
    # 3–5 TR foods templates (simple fixed templates proportional to macros)
    templates = []
    # breakfast, lunch, dinner, snack
    templates.append({"meal":"Kahvaltı","items":[
        {"food":"Yulaf + süt/yoğurt","approx":"60g yulaf"},
        {"food":"Yumurta","approx":"3 adet"},
        {"food":"Muz","approx":"1 adet"}
    ]})
    templates.append({"meal":"Öğle","items":[
        {"food":"Pirinç pilavı (basmati)","approx":"150g pişmiş"},
        {"food":"Tavuk göğsü","approx":"160g"},
        {"food":"Zeytinyağlı salata","approx":"1-2 yk"}
    ]})
    templates.append({"meal":"Akşam","items":[
        {"food":"Bulgur/Patates","approx":"200g pişmiş"},
        {"food":"Kırmızı et / Köfte","approx":"150g"},
        {"food":"Yoğurt","approx":"150g"}
    ]})
    templates.append({"meal":"Ara Öğün","items":[
        {"food":"Lor/Light peynir + tam buğday ekmek","approx":"2 dilim"},
        {"food":"Fındık/Badem","approx":"20-25g"}
    ]})
    return templates[:4]

def build_nutrition(sex: str, age: int, height_cm: float, weight_kg: float, goal: str, days_per_week: int, session_minutes: int) -> Dict[str, Any]:
    bmr = mifflin(height_cm, weight_kg, age, sex)
    tdee = bmr * activity_multiplier(days_per_week, session_minutes)
    target = adjust_goal(tdee, goal)
    calories = int(round(target))
    mac = macros_from_goals(weight_kg, goal)
    carbs = carbs_from_rest(calories, mac["protein_g"], mac["fat_g"])
    plan = {
        "calories": calories,
        "protein_g": mac["protein_g"],
        "fat_g": mac["fat_g"],
        "carbs_g": carbs,
        "templates": meal_templates_tr(mac["protein_g"], carbs, mac["fat_g"])
    }
    return plan
