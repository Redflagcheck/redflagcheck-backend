from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import User, Analysis
import base64
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import render
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
import logging
from django.utils.crypto import get_random_string
from redflagcheck.utils.magic_links import send_magic_link
from django.utils import timezone
from PIL import Image
import pytesseract
import io
import os
import openai
from pathlib import Path
from redflagcheck.utils.parsers import parse_why_q
from django.conf import settings



BASE_DIR = Path(__file__).resolve().parent.parent  # Projectroot
PROMPT_PATH = BASE_DIR / "redflagcheck" / "prompts" / "prompt_verdieping.txt"

PROMPTS_DIR = BASE_DIR / "redflagcheck" / "prompts"
P_ANALYSE = (PROMPTS_DIR / "prompt_analyse.txt").read_text(encoding="utf-8")
P_OUTPUT  = (PROMPTS_DIR / "analysis_output.txt").read_text(encoding="utf-8")

openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")


# ——— Diagnostics ———
logging.basicConfig(level=logging.INFO)
try:
    openai_version = getattr(openai, "__version__", "unknown")
except Exception:
    openai_version = "unknown"
logging.warning(f"[Diag] OpenAI lib version: {openai_version}")
logging.warning(f"[Diag] OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
logging.warning(f"[Diag] PROMPT_PATH: {PROMPT_PATH} exists={PROMPT_PATH.exists()}")

def chat_complete(model: str, messages: list, temperature: float = 0.2, max_tokens: int = 220) -> str:
    """
    Compatibele wrapper voor OpenAI 1.x (client.chat.completions) en als fallback 0.x (ChatCompletion).
    Retourneert altijd de .content string.
    """
    try:
        # Probeer 1.x stijl eerst (jouw omgeving draait 1.99.4)
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            # Fallback naar 0.x (voor het geval je lokaal wisselt)
            if hasattr(openai, "ChatCompletion"):
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content.strip()
            raise
    except Exception as e:
        logging.exception(f"[OpenAI] chat_complete error: {e}")
        raise


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def home(request):
    return HttpResponse("RedFlagCheck werkt!")

def generate_unique_token():
    while True:
        token = get_random_string(48)
        if not User.objects.filter(token=token).exists():
            return token

def extract_ocr_from_base64(base64_str):
    try:
        # Verwijder eventueel data:image/png;base64, etc.
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        imgdata = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(imgdata))
        ocr_text = pytesseract.image_to_string(image, lang="nld+eng")
        return ocr_text.strip()
    except Exception as e:
        return f"[OCR Error: {str(e)}]"


@api_view(['POST'])
@permission_classes([AllowAny])
def form_submit(request):
    logging.info("[RedFlagCheck] Nieuw formulier ontvangen.")

    email = (request.data.get('email') or "").strip().lower()
    name = request.data.get('name', '').strip()
    message = request.data.get('message', '').strip()
    context = request.data.get('context', '').strip()

    screenshot_file = request.FILES.get('screenshot')
    base64_data = request.data.get('screenshot_url', '')
    ocr_input = request.data.get('ocr', '').strip()
    question1 = request.data.get('question1', '').strip()
    answer1 = request.data.get('answer1', '').strip()
    question2 = request.data.get('question2', '').strip()
    answer2 = request.data.get('answer2', '').strip()
    result = request.data.get('result', '').strip()
    gpt_result_html = request.data.get('gpt_result_html', '').strip()

    # --- VALIDATIE ---
    if not email or (not message and not screenshot_file and not (base64_data and base64_data.startswith('data:image'))):
        logging.warning("[RedFlagCheck] Ongeldige inzending: ontbrekende velden.")
        return Response({'status': 'error', 'message': 'E-mail en minimaal één van bericht of screenshot zijn verplicht.'}, status=400)

    # --- SCHERMAFBEELDING OPSLAAN ---
    screenshot_url = ''
    ocr_text = ''
    if screenshot_file:
        path = default_storage.save('uploads/' + screenshot_file.name, screenshot_file)
        screenshot_url = default_storage.url(path)
        # (optioneel) OCR uitvoeren op file kan later als nodig
    elif base64_data and base64_data.startswith('data:image'):
        try:
            format, imgstr = base64_data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f"uploads/base64_{email.replace('@','_')}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=file_name)
            path = default_storage.save(file_name, data)
            screenshot_url = default_storage.url(path)
            # OCR direct uitvoeren op base64
            ocr_text = extract_ocr_from_base64(base64_data)
        except Exception as e:
            logging.error(f"Screenshot verwerken/OCR mislukt: {e}")
            ocr_text = ""
    else:
        screenshot_url = ''
        ocr_text = ''

    # Als OCR niet nieuw gemaakt, pak uit formulier (mag leeg zijn)
    if not ocr_text:
        ocr_text = ocr_input

    # --- GEBRUIKER AANMAKEN/OPHALEN ---
    user, _ = User.objects.get_or_create(email=email, defaults={'name': name})

    # --- ANALYSE OPSLAAN ---
    analysis = Analysis.objects.create(
        user=user,
        user_email=email,
        message=message,
        context=context,
        screenshot_url=screenshot_url,
        ocr=ocr_text,
        question1=question1,
        answer1=answer1,
        question2=question2,
        answer2=answer2,
        result=result,
        gpt_result_html=gpt_result_html
    )

    logging.info(f"[RedFlagCheck] Analyse opgeslagen (id: {analysis.analysis_id}) voor {email}")
    return Response({'status': 'success', 'analysis_id': analysis.analysis_id})




@api_view(['POST'])
@permission_classes([AllowAny])
def payment_success(request):
    logging.warning("==== PAYMENT SUCCESS DEBUG START ====")
    logging.warning(f"RAW REQUEST DATA: {request.data}")

    email = request.data.get('email')
    amount = request.data.get('amount')
    token = request.data.get('token', None)
    logging.warning(f"Request received - email: {email}, amount: {amount}, token: {token}")

    try:
        amount_float = float(amount)
        logging.warning(f"Amount as float: {amount_float}")
    except Exception as ex:
        logging.error(f"Invalid amount: {amount} ({ex})")
        return Response({'success': False, 'error': 'Invalid amount'}, status=400)

    credits = 0
    if abs(amount_float - 1) < 0.01:
        credits = 1
    elif abs(amount_float - 1.9) < 0.01:
        credits = 2
    elif abs(amount_float - 4.5) < 0.01:
        credits = 5
    logging.warning(f"Calculated credits: {credits} for amount: {amount_float}")

    if not email or credits == 0:
        logging.error(f"Invalid data: email={email} credits={credits}")
        return Response({'success': False, 'error': 'Invalid data'}, status=400)

    email_normalized = (email or "").strip().lower()
    try:
        token_to_use = generate_unique_token()
        user, created = User.objects.get_or_create(
            email=email_normalized,
            defaults={
                "token": token_to_use,
                "balance": credits,
                "email_verified": False,
                "password_hash": "",
            }
        )

        
        logging.warning(f"[DEBUG] created: {created}, email_verified: {user.email_verified}, magic_code: {user.magic_code}")


        if created or (not user.email_verified and not user.magic_code):
            logging.warning(f"[PAYMENT] Start sending magic link to: {user.email} (token: {user.token})")
            from redflagcheck.utils.magic_links import send_magic_link
            send_magic_link(user.email, user.token)
            logging.warning(f"[PAYMENT] send_magic_link() called for: {user.email}")

        if not created:
            if not user.token:
                user.token = token_to_use
            user.balance += credits
            user.save()

        logging.warning(f"User {email_normalized} → saldo: {user.balance}, token: {user.token}")
        logging.warning("==== PAYMENT SUCCESS DEBUG END ====")
        return Response({'success': True, 'token': user.token})

    except Exception as ex:
        logging.error(f"Onverwachte fout bij betaling: {ex}")
        return Response({'success': False, 'error': f'Unexpected error: {ex}'}, status=500)



@api_view(['POST'])
@permission_classes([AllowAny])
def verify_token(request):
    token = request.data.get('token')

    if not token:
        return Response({'success': False, 'error': 'No token provided'}, status=400)

    try:
        user = User.objects.get(token=token)
        return Response({
            'success': True,
            'email_verified': user.email_verified,
            'balance': user.balance,
            'saldo_ok': user.balance > 0
        })
    except User.DoesNotExist:
        return Response({'success': False, 'error': 'Invalid token'}, status=404)
    



@api_view(['POST'])
@permission_classes([AllowAny])
def start_analysis(request):
    """
    IN:  { "analysis_id": ... }
    OUT: { "status":"success", "reason_q1","question1","reason_q2","question2" }
         of { "status":"error", "message": ... }
    """
    analysis_id = request.data.get("analysis_id")
    if not analysis_id:
        return Response({"status": "error", "message": "Geen analysis_id opgegeven."}, status=400)

    try:
        analysis = Analysis.objects.get(analysis_id=analysis_id)
    except Analysis.DoesNotExist:
        return Response({"status": "error", "message": "Analyse niet gevonden."}, status=404)

    # Check saldo gebruiker (geen afschrijving in deze functie)
    if analysis.user.balance <= 0:
        return Response({
            "status": "redirect",
            "url": "/betaal/"
        }, status=200)

    # Prompt laden DIRECT uit bestand (veiliger)
    try:
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    except Exception as ex:
        logging.exception(f"[start_analysis] Prompt niet beschikbaar: {ex}")
        return Response({
            "status": "error",
            "message": "Interne fout: prompt niet beschikbaar. Probeer het later opnieuw."
        }, status=500)

    logging.info(
        f"[start_analysis] analysis_id={analysis_id} "
        f"msg_len={len(analysis.message or '')} "
        f"ocr_len={len(analysis.ocr or '')} "
        f"ctx_len={len(analysis.context or '')}"
    )

    # GPT-call met losse inputs
    try:
        gpt_reply = chat_complete(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Volg exact het gevraagde outputformat."},
                {"role": "user", "content": prompt_template},
                {"role": "user", "content": f"Bericht van de man:\n{analysis.message or ''}"},
                {"role": "user", "content": f"OCR-invoer:\n{analysis.ocr or ''}"},
                {"role": "user", "content": f"Extra context van gebruiker:\n{analysis.context or ''}"}
            ],
            temperature=0.2,
            max_tokens=220,
        )
        logging.info(f"[start_analysis] GPT reply (first 200): {gpt_reply[:200]!r}")

        parsed = parse_why_q(gpt_reply)
        if not parsed:
            return Response({
                "status": "error",
                "message": "Sorry, er is een fout opgetreden. OpenAI is momenteel even niet toegankelijk, probeer het over enkele ogenblikken nog eens. Uw tegoed is niet afgeschreven en blijft beschikbaar."
            }, status=500)

    except Exception as ex:
        logging.exception(f"[start_analysis] OpenAI error: {ex}")
        return Response({
            "status": "error",
            "message": "Sorry, er is een fout opgetreden. OpenAI is momenteel even niet toegankelijk, probeer het over enkele ogenblikken nog eens. Uw tegoed is niet gewijzigd."
        }, status=500)

    # Opslaan (geen saldo-wijziging in deze functie)
    analysis.reason_q1 = parsed["reason_q1"]
    analysis.question1 = parsed["question1"]
    analysis.reason_q2 = parsed["reason_q2"]
    analysis.question2 = parsed["question2"]
    analysis.save(update_fields=["reason_q1", "question1", "reason_q2", "question2", "updated_at"])

    return Response({"status": "success", **parsed}, status=200)




@api_view(['POST'])
@permission_classes([AllowAny])
def check_verification_status(request):
    token = request.data.get("token", "").strip()
    if not token:
        return Response({"success": False, "error": "Token ontbreekt"}, status=400)
    try:
        user = User.objects.get(token=token)
        if user.email_verified:
            return Response({"success": True, "status": "verified", "email": user.email})
        elif user.magic_code and user.magic_code_expiry and user.magic_code_expiry > timezone.now():
            return Response({"success": True, "status": "pending", "email": user.email,
                            "message": "E-mail is nog niet bevestigd. We hebben je een link gestuurd."})
        else:
            return Response({"success": True, "status": "expired", "email": user.email,
                            "message": "Je bevestigingslink is verlopen. Vraag een nieuwe aan."})
    except User.DoesNotExist:
        return Response({"success": False, "error": "Token ongeldig of gebruiker niet gevonden."}, status=404)

@api_view(['POST'])
@permission_classes([AllowAny])
def update_email(request):
    token = request.data.get("token", "").strip()
    new_email = request.data.get("new_email", "").strip().lower()
    if not token or not new_email:
        return Response({"success": False, "error": "Token en/of nieuw e-mailadres ontbreekt"}, status=400)
    try:
        user = User.objects.get(token=token)
        if user.email_verified:
            return Response({"success": False, "error": "E-mailadres kan niet meer aangepast worden nadat het is geverifieerd."}, status=400)
        # Check of email al bestaat bij andere user
        if User.objects.filter(email=new_email).exclude(token=token).exists():
            return Response({"success": False, "error": "Dit e-mailadres is al in gebruik."}, status=400)
        user.email = new_email
        user.email_verified = False
        user.save()
        send_magic_link(user.email, user.token)
        return Response({"success": True})
    except User.DoesNotExist:
        return Response({"success": False, "error": "Token ongeldig of gebruiker niet gevonden."}, status=404)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_magic_link(request):
    token = request.data.get("token", "").strip()
    if not token:
        return Response({"success": False, "error": "Token ontbreekt"}, status=400)
    try:
        user = User.objects.get(token=token)
        if user.email_verified:
            return Response({"success": False, "error": "E-mail is al geverifieerd"}, status=400)
        send_magic_link(user.email, token)
        return Response({"success": True})
    except User.DoesNotExist:
        return Response({"success": False, "error": "Gebruiker niet gevonden"}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_magic_link(request):
    token = request.data.get("token", "").strip()
    code = request.data.get("code", "").strip()

    if not token or not code:
        return Response({"success": False, "error": "Token en/of code ontbreekt"}, status=400)

    try:
        user = User.objects.get(token=token)

        # Check code én of de magic link nog geldig is
        if (
            user.magic_code == code and
            user.magic_code_expiry and
            user.magic_code_expiry > timezone.now()
        ):
            user.email_verified = True
            user.magic_code = None  # Code opmaken na gebruik (optioneel, extra veilig)
            user.magic_code_expiry = None
            user.save()
            return Response({"success": True, "message": "E-mailadres is succesvol geverifieerd."})
        else:
            return Response({"success": False, "error": "De link is ongeldig of verlopen."}, status=400)

    except User.DoesNotExist:
        return Response({"success": False, "error": "Gebruiker niet gevonden."}, status=404)



@api_view(['POST'])
@permission_classes([AllowAny])
def complete_analysis(request):
    """
    IN:  { analysis_id, [optioneel answer1, answer2 als je ze toch wil meesturen] }
    OUT (success): {
        success: True,
        html: "<HTML snippet>",
        result: "platte tekst",
        email_verified: bool,
        email: "...",
        balance: <int>
    }
    OUT (tegoed op): {
        status: "redirect",
        url: "/betaal/",
        balance: <int>
    }
    OUT (fout): {
        success: False,
        message: "foutmelding",
        balance: <int>
    }
    """

    analysis_id = request.data.get("analysis_id")
    answer1_in = (request.data.get("answer1") or "").strip()
    answer2_in = (request.data.get("answer2") or "").strip()

    if not analysis_id:
        return Response({"success": False, "message": "Geen analysis_id opgegeven."}, status=400)

    try:
        analysis = Analysis.objects.get(analysis_id=analysis_id)
    except Analysis.DoesNotExist:
        return Response({"success": False, "message": "Analyse niet gevonden."}, status=404)

    user = analysis.user

    # 1) Saldo check — bij onvoldoende saldo: frontend regelt redirect.
    if user.balance <= 0:
        return Response({"status": "redirect", "url": "/betaal/", "balance": user.balance}, status=200)

    # 2) Optioneel binnengekomen antwoorden opslaan (nu saldo OK is)
    fields_to_update = []
    if answer1_in:
        analysis.answer1 = answer1_in
        fields_to_update.append("answer1")
    if answer2_in:
        analysis.answer2 = answer2_in
        fields_to_update.append("answer2")
    if fields_to_update:
        fields_to_update.append("updated_at")
        analysis.save(update_fields=fields_to_update)

    # 3) Prompt & HTML-sjabloon on-demand inladen
    try:
        prompt_text = (PROMPTS_DIR / "prompt_analyse.txt").read_text(encoding="utf-8")
        output_tpl = (PROMPTS_DIR / "analysis_output.txt").read_text(encoding="utf-8")
    except Exception as ex:
        logging.exception(f"[complete_analysis] Prompt/template niet beschikbaar: {ex}")
        return Response(
            {"success": False, "message": "Interne fout: prompt niet beschikbaar.", "balance": user.balance},
            status=500
        )

    # 4) GPT-call met losse inputs (één call)
    try:
        gpt_text = chat_complete(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Je bent RedFlag AI – voer de analyse uit in het Nederlands. Geef uitsluitend platte tekst (geen HTML of Markdown)."},
                {"role": "user", "content": prompt_text},
                {"role": "user", "content": f"Bericht van de man:\n{analysis.message or ''}"},
                {"role": "user", "content": f"OCR-tekst uit screenshot (optioneel):\n{analysis.ocr or ''}"},
                {"role": "user", "content": f"Context / aanvullende informatie van de gebruiker (optioneel):\n{analysis.context or ''}"},
                {"role": "user", "content": f"Reden vraag 1:\n{analysis.reason_q1 or ''}"},
                {"role": "user", "content": f"Vraag 1:\n{analysis.question1 or ''}"},
                {"role": "user", "content": f"Antwoord op verdiepende vraag 1:\n{analysis.answer1 or ''}"},
                {"role": "user", "content": f"Reden vraag 2:\n{analysis.reason_q2 or ''}"},
                {"role": "user", "content": f"Vraag 2:\n{analysis.question2 or ''}"},
                {"role": "user", "content": f"Antwoord op verdiepende vraag 2:\n{analysis.answer2 or ''}"},
            ],
            temperature=0.2,
            max_tokens=900,
        )
    except Exception as ex:
        logging.exception(f"[complete_analysis] OpenAI error: {ex}")
        return Response(
            {
                "success": False,
                "message": "Sorry, er is een fout opgetreden. OpenAI is momenteel even niet toegankelijk, probeer het later nog eens. Uw tegoed is niet gewijzigd.",
                "balance": user.balance,
            },
            status=503,
        )

    if not gpt_text or not gpt_text.strip():
        return Response(
            {
                "success": False,
                "message": "Sorry, er is een fout opgetreden bij het genereren van de analyse. Uw tegoed is niet gewijzigd.",
                "balance": user.balance,
            },
            status=500,
        )

    # 5) HTML renderen via vaste template (geen tweede GPT-call)
    html_snippet = (
        output_tpl
            .replace("[BERICHT_VAN_DE_MAN]", analysis.message or "")
            .replace("[OCR_INVOER]", analysis.ocr or "")
            .replace("[GEBRUIKERS_CONTEXT]", analysis.context or "")
            .replace("[VRAAG_1]", analysis.question1 or "")
            .replace("[ANTWOORD_1]", analysis.answer1 or "")
            .replace("[VRAAG_2]", analysis.question2 or "")
            .replace("[ANTWOORD_2]", analysis.answer2 or "")
            .replace("{{GPT_ANTWOORD}}", gpt_text)
    )

    # 6) Opslaan (GEEN saldo-wijziging hier)
    analysis.result = gpt_text
    analysis.gpt_result_html = html_snippet
    analysis.save(update_fields=["result", "gpt_result_html", "updated_at"])

    # 7) Succesresponse
    return Response(
        {
            "success": True,
            "html": html_snippet,
            "result": gpt_text,
            "email_verified": bool(user.email_verified),
            "email": user.email,
            "balance": user.balance,
        },
        status=200,
    )

# backend/redflagcheck/views.py  — voeg deze functie toe (onder je andere API views)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from .models import User, Analysis

@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_analysis_viewed(request):
    """
    IN:  { "analysis_id": <int> }
    OUT 200: { "success": true, "analysis_id": <int>, "charged": true, "balance": <int> }
    OUT 402: { "status": "redirect", "url": "/betaal/", "balance": <int> }
    OUT 409: { "success": false, "message": "Result not ready" }
    OUT 400/404: { "success": false, "message": "..." }
    """
    analysis_id = request.data.get("analysis_id")
    if not analysis_id:
        return Response({"success": False, "message": "analysis_id missing"}, status=400)

    try:
        analysis = Analysis.objects.select_related("user").get(analysis_id=analysis_id)
    except Analysis.DoesNotExist:
        return Response({"success": False, "message": "Analysis not found"}, status=404)

    user = analysis.user

    # Result moet bestaan voordat we mogen afschrijven
    if not (analysis.result or analysis.gpt_result_html):
        return Response({"success": False, "message": "Result not ready"}, status=409)

    # Idempotent: al afgerekend → geen nieuwe afschrijving
    if analysis.is_charged:
        return Response(
            {"success": True, "analysis_id": analysis.analysis_id, "charged": True, "balance": user.balance},
            status=200,
        )

    # Nog niet afgerekend → saldo vereist
    if user.balance <= 0:
        return Response({"status": "redirect", "url": "/betaal/", "balance": user.balance}, status=402)

    # Atomic charge (race-condition safe)
    with transaction.atomic():
        u = User.objects.select_for_update().get(pk=user.pk)
        if u.balance <= 0:
            return Response({"status": "redirect", "url": "/betaal/", "balance": u.balance}, status=402)

        u.balance = u.balance - 1
        u.save(update_fields=["balance"])

        analysis.is_charged = True
        analysis.charged_at = timezone.now()
        analysis.save(update_fields=["is_charged", "charged_at", "updated_at"])

    return Response(
        {"success": True, "analysis_id": analysis.analysis_id, "charged": True, "balance": u.balance},
        status=200,
    )
