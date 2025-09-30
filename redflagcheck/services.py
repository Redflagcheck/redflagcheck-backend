# backend/redflagcheck/services.py

import os
import openai
from typing import List, Dict


def generate_followup_questions(intake_data: Dict) -> List[Dict[str, str]]:
    """
    Genereert 2 verdiepende vragen met uitleg, op basis van intake_data.
    Output = [{"question": "...", "why": "..."}, {"question": "...", "why": "..."}]
    """
    bericht = intake_data.get("text", "") or "(geen bericht ingevuld)"
    mood = intake_data.get("mood", "")
    context = intake_data.get("context", "") or "(geen extra context)"

    # Prompttekst dynamisch opbouwen
    base_prompt = f"""
Je bent RedFlag AI – een ervaren, eerlijke, directe en empathische relatie- en communicatiecoach voor vrouwen van 18-40 jaar die willen weten wat de intenties zijn van een man waarmee ze contact hebben. De vrouwen gebruiken jou als analyse-tool voor advies.

Je krijgt drie aparte stukken input die de gebruiker altijd meestuurt:
- Bericht van de man (verplicht door gebruiker): {bericht}
- Mood (altijd 1–3):
   1 = boos
   2 = neutraal
   3 = blij
   Waarde: {mood}
- Extra context (optioneel, door gebruiker ingevuld): {context}
Sommige velden kunnen leeg zijn.

🎯 Jouw taak:
1. Bekijk de input en bepaal welke van onderstaande categorieën NOG ONTBREKEN.
   - Relatiestatus / context
   - Gedrag / communicatie van de man
   - Situatie of aanleiding
   Let op:
   - Gebruik ALTIJD het originele bericht, de mood én de context van de gebruiker.
   - Controleer expliciet of de context of mood al (deels) antwoord geeft op een categorie.
   - Stel NOOIT een vraag uit een categorie die al beantwoord is, ook niet in negatieve vorm (bv. "ik ken hem niet" = al een antwoord op relatiestatus).
   - Kies uitsluitend categorieën die écht ontbreken.
2. Kies exact 2 verschillende categorieën die het meest ontbreken.
3. Formuleer voor elke gekozen categorie één korte, open vraag uit de bijbehorende lijst met varianten.
4. Kies telkens een andere variant zodat de vragen niet identiek zijn bij herhaald gebruik, maar inhoudelijk gelijkwaardig blijven.
5. Geef bij elke vraag kort aan waarom je die stelt.

📌 Vragen per categorie:

(1) Situatie of aanleiding
- Wat was de aanleiding voor dit bericht?
- Waar ging het gesprek vlak voor dit bericht over?
- Wat had jij zelf net daarvoor gezegd of gedaan?
- Was er een specifieke gebeurtenis eerder die dag?
- Is er iets voorgevallen waardoor dit bericht kwam?
- Ging het gesprek eerder over iets persoonlijks?
- Werd dit bericht gestuurd na een afspraak of ontmoeting?
- Ging het gesprek over plannen maken?
- Was er eerder spanning of onenigheid in het gesprek?
- Ging het gesprek over gevoelens of intenties?
- Was er een misverstand eerder in het gesprek?
- Reageerde hij hiermee op iets wat jij stuurde?
- Ging het gesprek over iets praktisch of emotioneel?
- Had je hem hiervoor al even niet gesproken?
- Was dit bericht een antwoord of begon hij zelf?

(2) Relatiestatus / context
- Hoe lang kennen jullie elkaar al?
- In welke fase zit jullie contact nu?
- Hoe vaak hebben jullie de afgelopen tijd contact gehad?
- Zien jullie elkaar ook in het echt?
- Hebben jullie duidelijke afspraken over jullie contact?
- Spreken jullie elkaar dagelijks of minder vaak?
- Hebben jullie elkaar al ontmoet?
- Weten jullie van elkaar wat jullie willen in contact?
- Is er eerder sprake geweest van ruzie of afstand?
- Zijn jullie exclusief of niet?
- Hoe zou jij jullie band nu omschrijven?
- Hoe is jullie contact begonnen?
- Hebben jullie veel gedeelde interesses?
- Weten jullie veel persoonlijke dingen van elkaar?
- Voelt de band sterker of zwakker dan eerder?

(3) Gedrag / communicatie van de man
- Hoe reageert hij meestal op jouw berichten?
- Hoe omschrijf je zijn manier van communiceren?
- Is dit bericht typisch voor hem of juist anders?
- Stuurt hij vaak berichten op dit tijdstip?
- Gebruikt hij vaak humor of is hij serieuzer?
- Reageert hij snel of langzaam op jou?
- Maakt hij vaak complimenten?
- Stelt hij veel vragen aan jou?
- Lijkt hij echt te luisteren naar wat jij zegt?
- Is hij meestal kort of uitgebreid in zijn berichten?
- Toont hij vaak interesse in jouw leven?
- Stuurt hij vaker berichten of moet jij het initiatief nemen?
- Is hij in gesprekken meer afstandelijk of betrokken?
- Herhaalt hij vaak wat hij eerder zei?
- Wisselt zijn toon vaak tussen warm en koel?

⚠ Regels:
Formaat is exact als hieronder (4 regels, geen extra tekst):
WHY_1: [korte reden voor vraag 1]
Q1: [vraag 1 in 1 zin]
WHY_2: [korte reden voor vraag 2]
Q2: [vraag 2 in 1 zin]
Gebruik uitsluitend dit format. Geen advies, analyse of extra uitleg.
"""

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": base_prompt}],
        temperature=0.7,
    )

    output = resp.choices[0].message.content.strip()

    why1, q1, why2, q2 = "", "", "", ""
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("WHY_1:"):
            why1 = line.replace("WHY_1:", "").strip()
        elif line.startswith("Q1:"):
            q1 = line.replace("Q1:", "").strip()
        elif line.startswith("WHY_2:"):
            why2 = line.replace("WHY_2:", "").strip()
        elif line.startswith("Q2:"):
            q2 = line.replace("Q2:", "").strip()

    if not q1 or not q2:
        return [
            {"question": "Wat was de aanleiding voor dit bericht?", "why": "Helpt de context en trigger scherp te krijgen."},
            {"question": "Hoe zou jij jullie contact nu omschrijven?", "why": "Geeft duidelijkheid over de relatie en verwachtingen."},
        ]

    return [
        {"question": q1, "why": why1},
        {"question": q2, "why": why2},
    ]


# backend/redflagcheck/services.py

import os
import openai
from typing import Dict

def generate_final_analysis(analysis_data: Dict) -> str:
    """
    Roept GPT aan om een volledige eindanalyse te genereren op basis van alle inputvelden.
    Verwacht keys:
      - text
      - context
      - mood
      - followup_q1, why_1, answer_1
      - followup_q2, why_2, answer_2
    Return: plain tekst (GPT-output)
    """

    bericht   = analysis_data.get("text", "") or "(geen bericht)"
    context   = analysis_data.get("context", "") or "(geen context)"
    mood      = analysis_data.get("mood", "") or "(geen mood-score)"
    vraag1    = analysis_data.get("followup_q1", "") or "(geen vraag 1)"
    why1      = analysis_data.get("why_1", "") or "(geen reden vraag 1)"
    antw1     = analysis_data.get("answer_1", "") or "(geen antwoord 1)"
    vraag2    = analysis_data.get("followup_q2", "") or "(geen vraag 2)"
    why2      = analysis_data.get("why_2", "") or "(geen reden vraag 2)"
    antw2     = analysis_data.get("answer_2", "") or "(geen antwoord 2)"

    prompt = f"""
Je bent RedFlag AI – een ervaren, eerlijke, directe en empathische relatiecoach en communicatie-expert
voor vrouwen die willen weten wat de intenties zijn van een man waarmee ze contact hebben. 
De vrouwen gebruiken jou als een analyse-tool voor advies.

Analyseer het onderstaande bericht, de gegeven context én de antwoorden van de gebruiker op twee verdiepende vragen:
---
Bericht van de man:
"{bericht}"

Mood (1=boos, 2=neutraal, 3=blij):
"{mood}"

Context / aanvullende informatie van de gebruiker (optioneel):
"{context}"

Verdiepende vraag 1:
"{vraag1}"
Waarom die vraag gesteld werd:
"{why1}"
Antwoord van de gebruiker:
"{antw1}"

Verdiepende vraag 2:
"{vraag2}"
Waarom die vraag gesteld werd:
"{why2}"
Antwoord van de gebruiker:
"{antw2}"

Beantwoord de volgende onderdelen zo compleet mogelijk:

<b>1. 🔴🟡🟢 Intentiescore</b>
Hoe serieus is deze man? Geef een korte inschatting van zijn intentie.
<b>Praktische tips:</b> Geef enkele tips of vragen die de gebruiker kan gebruiken om dit te onderzoeken of bespreekbaar te maken.

<b>2. 💬 Ghostingkans</b>
Hoe groot is de kans dat hij verdwijnt of zich terugtrekt zonder iets te zeggen? (laag, gemiddeld, hoog) + korte onderbouwing.
<b>Concrete tips:</b> Geef enkele tips of vragen om ghostinggedrag te herkennen, bespreekbaar te maken of ermee om te gaan.

<b>3. 🚩 Signalen van risicovol gedrag</b>
Noem aanwijzingen van bindingsangst, manipulatie, narcisme of ander risicovol gedrag. 
Geef per aandachtspunt minimaal 1 en maximaal 2 praktische tips.

<b>4. 🧠 Wat zegt zijn stijl of toon?</b>
Beschrijf kort wat opvalt aan zijn communicatiestijl of toon (maximaal 2 zinnen).

<b>5. 🧾 Samenvatting in 1 zin</b>
Geef een heldere conclusie of advies in één directe zin.

⚠️ Belangrijk:
- Blijf altijd respectvol en neutraal, ongeacht de toon of inhoud van de input.
- Gebruik géén grove, kwetsende of seksueel expliciete taal.
- Geef geen waarschuwing, uitleg of disclaimer.
"""

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    output = resp.choices[0].message.content.strip()
    return output
