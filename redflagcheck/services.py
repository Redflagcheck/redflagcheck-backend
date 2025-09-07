# services.py
import openai
import os
from typing import List, Dict

def generate_followup_questions(intake_data: Dict) -> List[str]:
    """
    Genereert 2 verdiepende vragen met uitleg, op basis van intake_data.
    Gebruikt prompt uit promt_verdieping.txt.
    """
    # Variabelen uit intake_data
    bericht = intake_data.get("text", "")
    mood = intake_data.get("mood", "")
    context = intake_data.get("context", "")

    # Prompt inladen
    with open(os.path.join(os.path.dirname(__file__), "prompts/prompt_verdieping.txt"), "r", encoding="utf-8") as f:
        base_prompt = f.read()

    # Prompt invullen
    prompt = base_prompt.replace("[BERICHT_VAN_DE_MAN]", bericht)\
                        .replace("[mood]", mood)\
                        .replace("[GEBRUIKERS_CONTEXT]", context)

    # GPT-call
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    output = resp.choices[0].message.content.strip()

    # Verwachte format:
    # WHY_1: ...
    # Q1: ...
    # WHY_2: ...
    # Q2: ...

    questions = []
    for line in output.splitlines():
        if line.startswith("Q1:"):
            questions.append(line.replace("Q1:", "").strip())
        elif line.startswith("Q2:"):
            questions.append(line.replace("Q2:", "").strip())

    # Altijd 2 vragen teruggeven (anders fallback)
    if len(questions) < 2:
        questions = [
            "Hoe voel jij je bij dit bericht?",
            "Hoe zou jij jullie contact nu omschrijven?",
        ]

    return questions

def run_ocr_from_url_or_blank(intake_data: Dict) -> str:
    """
    Placeholder OCR: als er een screenshot_url staat, return lege string
    (later echte OCR). Zonder screenshot → ook lege string.
    """
    screenshot_url = intake_data.get("screenshot_url") or intake_data.get("screenshot")
    if screenshot_url:
        return ""  # later echte OCR-resultaat
    return ""
