# backend/redflagcheck/services.py

import os
import openai
from typing import List, Dict

def generate_followup_questions(intake_data: Dict) -> List[Dict[str, str]]:
    """
    Genereert 2 verdiepende vragen met uitleg, op basis van intake_data.
    Output = [{"question": "...", "why": "..."}, {"question": "...", "why": "..."}]
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

    # Verwacht format:
    # WHY_1: ...
    # Q1: ...
    # WHY_2: ...
    # Q2: ...

    why1, q1, why2, q2 = "", "", "", ""
    for line in output.splitlines():
        if line.startswith("WHY_1:"):
            why1 = line.replace("WHY_1:", "").strip()
        elif line.startswith("Q1:"):
            q1 = line.replace("Q1:", "").strip()
        elif line.startswith("WHY_2:"):
            why2 = line.replace("WHY_2:", "").strip()
        elif line.startswith("Q2:"):
            q2 = line.replace("Q2:", "").strip()

    # Fallback als GPT niet goed antwoordt
    if not q1 or not q2:
        return [
            {"question": "Wat was de aanleiding voor dit bericht?", "why": "Helpt de context en trigger scherp te krijgen."},
            {"question": "Hoe zou jij jullie contact nu omschrijven?", "why": "Geeft duidelijkheid over de relatie en verwachtingen."},
        ]

    return [
        {"question": q1, "why": why1},
        {"question": q2, "why": why2},
    ]
