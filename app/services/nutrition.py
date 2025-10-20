from __future__ import annotations
from typing import Dict, Any

def bmr(sex: str, age: int, height_cm: float, weight_kg: float) -> float:
    if sex and sex.lower().startswith("m"):
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

ACTIVITY = {2: 1.3, 3: 1.4, 4: 1.5, 5: 1.6, 6: 1.7}

def macros(goal: str, sex: str, age: int, height_cm: float, weight_kg: float, days_per_week: int) -> Dict[str, int]:
    _bmr = bmr(sex, age, height_cm, weight_kg)
    tdee = _bmr * ACTIVITY.get(days_per_week, 1.5)
    if goal == "cut":
        calories = int(tdee * 0.85)
    elif goal == "bulk":
        calories = int(tdee * 1.08)
    else:
        calories = int(tdee)
    p = round(weight_kg * 2.0)
    f = round(weight_kg * 0.8)
    kcal_pf = p * 4 + f * 9
    c = max(0, round((calories - kcal_pf) / 4))
    return {"calories": calories, "protein_g": p, "fat_g": f, "carb_g": c, "tdee": int(tdee)}

TR_MEALS = [
    {"name":"Kahvaltı — Yulaf & Yumurta","items":["Yulaf 80g","Süt light 250ml","Whey 1 ölçek (ops)","Yumurta 3","Muz 1"]},
    {"name":"Öğle — Tavuklu Pilav","items":["Pirinç 120g (çiğ)","Tavuk göğüs 180g","Zeytinyağı 10g","Salata"]},
    {"name":"Ara — Yoğurt & Granola","items":["Yoğurt light 200g","Granola 40g","Bal 10g"]},
    {"name":"Akşam — Kırmızı Et & Patates","items":["Dana yağsız 180g","Patates 400g","Zeytinyağı 10g","Sebze"]},
    {"name":"Gece — Peynir & Kraker","items":["Lor/az yağlı 150g","Tam tahıllı kraker 40g"]},
]

def meal_templates(_calories: int) -> list[dict[str, Any]]:
    return TR_MEALS[:5]