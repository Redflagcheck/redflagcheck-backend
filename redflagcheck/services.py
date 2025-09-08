# backend/redflagcheck/services.py
import os
from typing import List, Dict

import openai
import requests        # nieuw
import base64          # nieuw
from PIL import Image, ImageOps  # nieuw
import io              # nieuw


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
    Robuuste OCR:
    - Haal de image server-side op (met User-Agent)
    - Downscale/comprimeer als 'ie groot is
    - Stuur als base64 data-URI naar OpenAI (geen hotlink-gedoe)
    """
    screenshot_url = (
        intake_data.get("screenshot_url")
        or intake_data.get("screenshot")
        or intake_data.get("image_url")
    )
    if not screenshot_url:
        return ""

    try:
        # 1) Server-side ophalen (met UA header)
        UA = {"User-Agent": "RedFlagCheck/1.0"}
        r = requests.get(screenshot_url, timeout=15, headers=UA)
        if r.status_code != 200:
            print(f"[OCR] GET {r.status_code} for {screenshot_url}")
            return ""

        ctype = r.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            print(f"[OCR] Not an image Content-Type: {ctype}")
            return ""

        img_bytes = r.content

        # 2) Downscale/compress als te groot (>10 MB)
        if len(img_bytes) > 10 * 1024 * 1024:
            try:
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageOps.exif_transpose(img)  # respecteer EXIF-rotatie
                # converteer naar RGB (weg met alpha/indici)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                # begrens langste zijde tot 1600px
                img.thumbnail((1600, 1600))
                out = io.BytesIO()
                img.save(out, format="JPEG", quality=85, optimize=True)
                img_bytes = out.getvalue()
                ctype = "image/jpeg"
                print(f"[OCR] Downscaled to {len(img_bytes)} bytes")
            except Exception as e:
                print(f"[OCR] Downscale failed: {e} (using original bytes)")

        # 3) Base64 data-URI bouwen
        b64 = base64.b64encode(img_bytes).decode("ascii")
        data_uri = f"data:{ctype};base64,{b64}"

        # 4) GPT-4o aanroepen
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Lees ALLE tekst uit deze screenshot. Geef uitsluitend de ruwe tekst, zonder toelichting of formatting."
                },
                {"type": "image_url", "image_url": {"url": data_uri}},
            ],
        }]
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.0,
            max_tokens=2000,
        )
        return (resp.choices[0].message.content or "").strip()

    except Exception as e:
        print(f"[OCR] OCR failed: {e}")
        return ""