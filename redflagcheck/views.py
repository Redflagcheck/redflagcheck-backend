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




def home(request):
    return HttpResponse("RedFlagCheck werkt!")

def generate_unique_token():
    while True:
        token = get_random_string(48)
        if not User.objects.filter(token=token).exists():
            return token

@api_view(['POST'])
@permission_classes([AllowAny])
def form_submit(request):
    email = request.data.get('email')
    name = request.data.get('name', '')
    message = request.data.get('message')
    context = request.data.get('context', '')

    screenshot_file = request.FILES.get('screenshot')
    base64_data = request.data.get('screenshot_url', '')
    ocr = request.data.get('ocr', '')
    question1 = request.data.get('question1', '')
    answer1 = request.data.get('answer1', '')
    question2 = request.data.get('question2', '')
    answer2 = request.data.get('answer2', '')
    result = request.data.get('result', '')
    gpt_result_html = request.data.get('gpt_result_html', '')

    if not email or (not message and not screenshot_file and not (base64_data and base64_data.startswith('data:image'))):
        return Response({'status': 'error', 'message': 'E-mail en minimaal één van bericht of screenshot zijn verplicht.'}, status=400)

    screenshot_url = None
    if screenshot_file:
        path = default_storage.save('uploads/' + screenshot_file.name, screenshot_file)
        screenshot_url = default_storage.url(path)
    elif base64_data and base64_data.startswith('data:image'):
        format, imgstr = base64_data.split(';base64,')
        ext = format.split('/')[-1]
        file_name = f"uploads/base64_{email.replace('@','_')}.{ext}"
        data = ContentFile(base64.b64decode(imgstr), name=file_name)
        path = default_storage.save(file_name, data)
        screenshot_url = default_storage.url(path)
    else:
        screenshot_url = ''

    user, _ = User.objects.get_or_create(email=email, defaults={'name': name})

    analysis = Analysis.objects.create(
        user=user,
        user_email=email,
        message=message,
        context=context,
        screenshot_url=screenshot_url,
        ocr=ocr,
        question1=question1,
        answer1=answer1,
        question2=question2,
        answer2=answer2,
        result=result,
        gpt_result_html=gpt_result_html
    )

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

        if created:
            logging.warning(f"Nieuwe gebruiker aangemaakt: {email_normalized} met token {token_to_use}")
            from redflagcheck.utils.magic_links import send_magic_link
            send_magic_link(user.email, token_to_use)
        else:
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