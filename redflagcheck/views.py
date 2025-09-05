# backend/redflagcheck/views.py

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

from .models import Analysis


@csrf_exempt
def intake(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # 1) JSON veilig inlezen
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        return JsonResponse({"error": "Invalid JSON", "detail": str(e)}, status=400)

    # 2) Probeer te schrijven en log exact waarom het eventueel faalt
    try:
        analysis = Analysis.objects.create(data=body)
        return JsonResponse({"analysis_id": str(analysis.analysis_id)}, status=201)
    except Exception as e:
        return JsonResponse({"error": "DB write failed", "detail": str(e)}, status=500)

   


@csrf_exempt
def feedback(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        analysis_id = body.get("analysis_id")
        rating = body.get("rating")
        comment = body.get("comment", "")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not analysis_id:
        return JsonResponse({"error": "analysis_id required"}, status=400)

    try:
        analysis = Analysis.objects.get(analysis_id=analysis_id)
    except Analysis.DoesNotExist:
        return JsonResponse({"error": "analysis not found"}, status=404)

    # Voeg/overschrijf feedback in JSON
    data = analysis.data or {}
    data["feedback"] = {
        "rating": rating,
        "comment": comment,
        "rated_at": now().isoformat(),
    }
    analysis.data = data
    analysis.save(update_fields=["data"])

    return JsonResponse({"ok": True}, status=200)


@csrf_exempt
def request_verification(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        email = body.get("email")
        analysis_id = body.get("analysis_id")
        callback_url = body.get("callback_url")  # optioneel
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not email:
        return JsonResponse({"error": "email required"}, status=400)

    # Dummy response; later vervangen door echte magic-link flow
    return JsonResponse(
        {
            "ok": True,
            "message": f"Verification mail would be sent to {email}",
            "analysis_id": analysis_id,
            "callback_url": callback_url,
        },
        status=200,
    )

