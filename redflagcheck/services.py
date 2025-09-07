# services.py
from typing import List, Dict

def generate_followup_questions(intake_data: Dict) -> List[str]:
    """
    Heel simpele placeholder: 2 contextuele vragen.
    Later vervangen door GPT.
    """
    context = intake_data.get("context") or intake_data.get("text") or ""
    base = context[:120] + ("…" if len(context) > 120 else "")
    return [
        f"Wat mis ik in deze situatie: “{base}”?",
        "Wat wil je dat de AI vooral meeneemt in de analyse (1 ding)?",
    ]

def run_ocr_from_url_or_blank(intake_data: Dict) -> str:
    """
    Placeholder OCR: als er een screenshot_url staat, return lege string
    (later echte OCR). Zonder screenshot → ook lege string.
    """
    screenshot_url = intake_data.get("screenshot_url") or intake_data.get("screenshot")
    if screenshot_url:
        return ""  # later echte OCR-resultaat
    return ""
