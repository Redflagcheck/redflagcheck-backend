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

def home(request):
    return HttpResponse("RedFlagCheck werkt!")


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

    try:
        emails = list(User.objects.values_list('email', flat=True))
        logging.warning(f"Alle e-mails in database: {emails}")
    except Exception as ex:
        logging.error(f"Error ophalen e-mails uit database: {ex}")

    email_normalized = (email or "").strip().lower()
    logging.warning(f"Email uit request: '{email}' (genormaliseerd: '{email_normalized}')")

    try:
        logging.warning(f"Start user lookup met email__iexact='{email_normalized}'")
        user = User.objects.get(email__iexact=email_normalized)
        logging.warning(f"User gevonden: {user.email} - huidig saldo: {user.balance}")
    except User.DoesNotExist:
        logging.error(f"User niet gevonden voor: '{email_normalized}'")
        return Response({'success': False, 'error': 'User not found'}, status=404)
    except Exception as ex:
        logging.error(f"Onverwachte fout bij user lookup: {ex}")
        return Response({'success': False, 'error': f'Unexpected error: {ex}'}, status=500)

    try:
        user.balance += credits
        user.save()
        logging.warning(f"Saldo opgehoogd: nieuw saldo = {user.balance}")
    except Exception as ex:
        logging.error(f"Fout bij updaten saldo: {ex}")
        return Response({'success': False, 'error': f'Balance update failed: {ex}'}, status=500)

    logging.warning("==== PAYMENT SUCCESS DEBUG END ====")
    return Response({'success': True})
