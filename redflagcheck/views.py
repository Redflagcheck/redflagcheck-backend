from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import User, Analysis
from rest_framework.parsers import MultiPartParser, FormParser


# Create your views here.

from django.http import HttpResponse

def home(request):
    return HttpResponse("RedFlagCheck werkt!")



@api_view(['POST'])
@permission_classes([AllowAny])
def form_submit(request):
    # Ondersteunt nu ook file uploads!
    email = request.data.get('email')
    name = request.data.get('name', '')
    message = request.data.get('message')
    context = request.data.get('context', '')

    # Bestand ophalen uit FILES (optioneel)
    screenshot_file = request.FILES.get('screenshot')
    screenshot_url = None

    # Bestand opslaan als het bestaat
    if screenshot_file:
        from django.core.files.storage import default_storage
        path = default_storage.save('uploads/' + screenshot_file.name, screenshot_file)
        screenshot_url = default_storage.url(path)
    else:
        screenshot_url = request.data.get('screenshot_url', '')

    if not email or not message:
        return Response({'status': 'error', 'message': 'Email en bericht zijn verplicht.'}, status=400)

    user, _ = User.objects.get_or_create(email=email, defaults={'name': name})

    analysis = Analysis.objects.create(
        user=user,
        message=message,
        context=context,
        screenshot_url=screenshot_url
    )

    return Response({'status': 'success', 'analysis_id': analysis.analysis_id})