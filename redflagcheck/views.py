from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import User, Analysis

# Create your views here.

from django.http import HttpResponse

def home(request):
    return HttpResponse("RedFlagCheck werkt!")



@api_view(['POST'])
@permission_classes([AllowAny])
def form_submit(request):
    # 1. Gegevens uit POST-body halen
    email = request.data.get('email')
    name = request.data.get('name', '')
    message = request.data.get('message')
    context = request.data.get('context', '')
    screenshot_url = request.data.get('screenshot_url', '')

    if not email or not message:
        return Response({'status': 'error', 'message': 'Email en bericht zijn verplicht.'}, status=400)

    # 2. User ophalen of aanmaken
    user, _ = User.objects.get_or_create(email=email, defaults={'name': name})

    # 3. Analysis opslaan
    analysis = Analysis.objects.create(
        user=user,
        message=message,
        context=context,
        screenshot_url=screenshot_url
    )

    return Response({'status': 'success', 'analysis_id': analysis.analysis_id})
