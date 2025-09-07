# backend/redflagcheck/services.py
import openai
import os
from typing import List, Dict


def generate_followup_questions(intake_data: Dict) -> List[str]:
    """
    Genereert 2 verdiepende vragen met uitleg, op basis van intake_data.
    Gebruikt losse messages i.p.v. één string.
    """
    bericht = intake_data.get("text", "")
    mood = intake_data.get("mood", "")
    context = intake_data.get("context", "")

    # Prompt-template inladen
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "prompt_verdieping.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read()

    # Chat messages opbouwen
    messages = [
        {"role": "system", "content": "Je bent RedFlag AI – een ervaren, eerlijke, directe en empathische relatie- en communicatiecoach."},
        {"role": "user", "content": f"Bericht van de man: {bericht}"},
        {"role": "user", "content": f"Mood: {mood}"},
        {"role": "user", "content": f"Extra context van gebruiker: {context}"},
        {"role": "user", "content": base_prompt},
    ]

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
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
            "Wat was de aanleiding voor dit bericht?",
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

