# backend/redflagcheck/views.py

import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .models import Analysis
import uuid
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .services import generate_followup_questions
import logging
log = logging.getLogger(__name__)


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
        log.info("INTAKE created %s", analysis.analysis_id)
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



def _auth_ok(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    prefix = "Bearer "
    if not auth.startswith(prefix):
        return False
    token = auth[len(prefix):].strip()
    expected = getattr(settings, "RFC_API_KEY", None)
    return expected and token == expected


@require_http_methods(["GET"])
@csrf_exempt
def analysis_followup(request, analysis_id: str):
    if not _auth_ok(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    # 1) UUID valideren
    try:
        uuid.UUID(str(analysis_id))
    except Exception:
        return JsonResponse({"detail": "Invalid analysis_id"}, status=400)

    log.info("FOLLOWUP hit %s", analysis_id)

    # 2) Record ophalen
    try:
        a = Analysis.objects.get(analysis_id=analysis_id)
    except Analysis.DoesNotExist:
        log.warning("FOLLOWUP not found %s", analysis_id)
        return JsonResponse({"detail": "Not found"}, status=404)

    # 3) Alleen vragen (geen OCR)
    changed = False
    data = a.data or {}

    if not a.followup_questions:
        a.followup_questions = generate_followup_questions(data)
        changed = True

    if a.status == "intake":
        a.status = "followup_pending"
        changed = True

    if changed:
        a.save(update_fields=["followup_questions", "status"])

    return JsonResponse({
        "analysis_id": str(a.analysis_id),
        "status": a.status,
        "questions": (a.followup_questions or [])[:2],
    }, status=200)
