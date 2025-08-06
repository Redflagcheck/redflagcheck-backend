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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import User

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

    # CHECK KOMT ALTIJD VOOR HET OPSLAAN!
    if not email or (not message and not screenshot_file and not (base64_data and base64_data.startswith('data:image'))):
        return Response({'status': 'error', 'message': 'E-mail en minimaal één van bericht of screenshot zijn verplicht.'}, status=400)

    screenshot_url = None

    if screenshot_file:
        path = default_storage.save('uploads/' + screenshot_file.name, screenshot_file)
        screenshot_url = default_storage.url(path)
    else:
        if base64_data and base64_data.startswith('data:image'):
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
        message=message,
        context=context,
        screenshot_url=screenshot_url
    )

    return Response({'status': 'success', 'analysis_id': analysis.analysis_id})


@api_view(['POST'])
@permission_classes([AllowAny])
def payment_success(request):
    email = request.data.get('email')
    amount = request.data.get('amount')

    try:
        amount = float(amount)
    except Exception:
        return Response({'success': False, 'error': 'Invalid amount'}, status=400)

    credits = 0
    if abs(amount - 1) < 0.01:
        credits = 1
    elif abs(amount - 1.9) < 0.01:
        credits = 2
    elif abs(amount - 4.5) < 0.01:
        credits = 5

    if not email or credits == 0:
        return Response({'success': False, 'error': 'Invalid data'}, status=400)

    try:
        user = User.objects.get(email=email)
        user.balance += credits
        user.save()
        return Response({'success': True})
    except User.DoesNotExist:
        return Response({'success': False, 'error': 'User not found'}, status=404)

