import json
import os
import uuid
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from .models import Analysis, Followup, AuditEvent, AnalysisStatus, AuditSeverity

API_KEY = os.getenv("API_SHARED_SECRET")  # zet in Render env vars
ALLOWED_ORIGIN = os.getenv("CORS_ALLOWED_ORIGIN")  # bv. https://redflagcheck.nl


def _cors(resp):
    if ALLOWED_ORIGIN:
        resp["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
        resp["Vary"] = "Origin"
    resp["Access-Control-Allow-Headers"] = "Content-Type, X-WP-API-Key"
    resp["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

def _bad(msg, code=400):
    return _cors(JsonResponse({"detail": msg}, status=code))

def _ok(data, code=200):
    return _cors(JsonResponse(data, status=code))

def _auth_ok(request) -> bool:
    return request.headers.get("X-WP-API-Key") == API_KEY

def _parse_json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None

def _client_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = (xff.split(",")[0].strip() if xff else None) or request.META.get("REMOTE_ADDR")
    return ip


# ---- simpele “GPT” stubs (geen OCR) ----
def _gen_questions(input_text: str, mood_score: int | None):
    # Twee voorbeeldvragen met WHY. Pas later aan naar echte model-call.
    return [
        (1, "Wat gaf jou precies dit gevoel?", "Helpt de trigger en context scherp te krijgen."),
        (2, "Wat verwacht je dat hij doet in de komende week?", "Maakt intenties concreet en toetsbaar."),
    ]

def _final_analysis_text_html_json(input_text: str, answers: dict, mood_score: int | None):
    # Minimalistische eindanalyse zonder OCR/GPT.
    summary = "Samenvatting op basis van jouw tekst en antwoorden."
    risk = "medium" if (mood_score or 3) >= 3 else "low"
    flags = []
    if len(input_text) < 80:
        flags.append({"type": "low_context", "note": "Weinig context; overweeg extra details."})
    result_json = {
        "summary": summary,
        "risk_level": risk,
        "flags": flags,
        "answers": answers,
    }
    html = f"<h2>Analyse</h2><p>{summary}</p><p><strong>Risico:</strong> {risk}</p>"
    text = f"{summary} | Risk: {risk}"
    return text, html, result_json


# ---- API ----
@csrf_exempt
def analyze(request):
    if request.method == "OPTIONS":
        return _ok({"ok": True})
    if request.method != "POST":
        return _cors(HttpResponseNotAllowed(["POST", "OPTIONS"]))
    if not _auth_ok(request):
        return _bad("Unauthorized", 401)

    body = _parse_json(request)
    if body is None:
        return _bad("Invalid JSON")

    mode = (body.get("mode") or "").strip().lower()
    if mode not in {"questions", "finalize"}:
        return _bad("mode must be 'questions' or 'finalize'")

    # shared fields
    wp_user_id = body.get("wp_user_id")
    mood_score = body.get("mood_score")
    input_text = (body.get("input_text") or "").strip()
    parent_id = body.get("parent_id")
    email = (body.get("email") or "").strip() or None
    name = (body.get("name") or "").strip() or None
    context = (body.get("context") or "").strip() or None

    if mode == "questions":
        if not input_text:
            return _bad("input_text is required")
        parent = None
        round_no = 1
        if parent_id:
            try:
                parent = Analysis.all_objects.get(analysis_id=uuid.UUID(str(parent_id)))
                round_no = parent.round + len(parent.children.all()) + 1
            except Analysis.DoesNotExist:
                return _bad("parent_id not found", 404)

        ip = _client_ip(request)

        with transaction.atomic():
            a = Analysis.all_objects.create(
                wp_user_id=wp_user_id,
                email=email,
                parent=parent,
                round=round_no,
                input_text=input_text,
                mood_score=mood_score,
                name=name,
                context=context,
                status=AnalysisStatus.QUESTIONS_READY,
                ip_address=ip,
            )

            questions = _gen_questions(a.input_text, a.mood_score)
            out = []
            for pos, q, why in questions:
                Followup.objects.create(
                    analysis=a,
                    position=pos,
                    question_text=q,
                    why=why,
                    answer_text="",  # wordt later ingevuld bij finalize
                    model_version="stub-v1",
                )
                out.append({"position": pos, "question": q, "why": why})

            AuditEvent.objects.create(
                wp_user_id=wp_user_id,
                type="analysis_started",
                severity=AuditSeverity.INFO,
                subject_ref=str(a.analysis_id),
                payload={"mode": "questions"},
                ip_address=ip,
            )

        return _ok({
            "analysis_id": str(a.analysis_id),
            "round": a.round,
            "questions": out,
            "status": a.status,
        })

    # mode == finalize
    analysis_id = body.get("analysis_id")
    answers = body.get("answers") or {}
    if not analysis_id:
        return _bad("analysis_id is required for finalize")
    try:
        a = Analysis.objects.get(analysis_id=uuid.UUID(str(analysis_id)))  # filters soft-deleted weg
    except (ValueError, Analysis.DoesNotExist):
        return _bad("analysis_id not found", 404)

    if not isinstance(answers, dict) or not answers:
        return _bad("answers must be a non-empty object keyed by position")

    with transaction.atomic():
        # vul antwoorden in de bestaande Followup records (positie 1..n)
        for k, v in answers.items():
            try:
                pos = int(k)
            except Exception:
                return _bad(f"answers keys must be integers, got {k!r}")
            fu = Followup.objects.filter(analysis=a, position=pos).first()
            if not fu:
                return _bad(f"no followup question at position {pos}", 400)
            fu.answer_text = (v or "").strip()
            fu.save(update_fields=["answer_text", "created_at"])

        a.status = AnalysisStatus.ANSWERS_SAVED
        a.save(update_fields=["status", "updated_at"])

        # eindanalyse (stub, geen OCR/GPT)
        text, html, json_obj = _final_analysis_text_html_json(a.input_text, answers, a.mood_score)
        a.result_text = text
        a.result_html = html
        a.result_json = json_obj
        a.status = AnalysisStatus.COMPLETED
        a.completed_at = timezone.now()
        a.save(update_fields=["result_text", "result_html", "result_json", "status", "completed_at", "updated_at"])

        AuditEvent.objects.create(
            wp_user_id=a.wp_user_id,
            type="analysis_completed",
            severity=AuditSeverity.INFO,
            subject_ref=str(a.analysis_id),
            payload={"answers_len": len(answers)},
            ip_address=_client_ip(request),
        )

    return _ok({
        "analysis_id": str(a.analysis_id),
        "status": a.status,
        "result": {"text": a.result_text, "html": a.result_html, "json": a.result_json},
    })


@csrf_exempt
def result(request, analysis_id: str):
    if request.method == "OPTIONS":
        return _ok({"ok": True})
    if request.method != "GET":
        return _cors(HttpResponseNotAllowed(["GET", "OPTIONS"]))
    if not _auth_ok(request):
        return _bad("Unauthorized", 401)

    try:
        a = Analysis.objects.get(analysis_id=uuid.UUID(str(analysis_id)))
    except (ValueError, Analysis.DoesNotExist):
        return _bad("Not found", 404)

    if a.status != AnalysisStatus.COMPLETED:
        return _bad("Analysis not completed yet", 409)

    return _ok({
        "analysis_id": str(a.analysis_id),
        "status": a.status,
        "result": {"text": a.result_text, "html": a.result_html, "json": a.result_json},
    })


@csrf_exempt
def audit_event(request):
    if request.method == "OPTIONS":
        return _ok({"ok": True})
    if request.method != "POST":
        return _cors(HttpResponseNotAllowed(["POST", "OPTIONS"]))
    if not _auth_ok(request):
        return _bad("Unauthorized", 401)

    body = _parse_json(request)
    if body is None:
        return _bad("Invalid JSON")

    ev_type = (body.get("type") or "").strip()
    if not ev_type:
        return _bad("type is required")

    AuditEvent.objects.create(
        wp_user_id=body.get("wp_user_id"),
        type=ev_type,
        severity=(body.get("severity") or "info").lower(),
        subject_ref=(body.get("subject_ref") or "").strip() or None,
        payload=body.get("payload") if isinstance(body.get("payload"), (dict, list)) else None,
        ip_address=_client_ip(request),
    )
    return _ok({"ok": True}, 201)


@csrf_exempt
def analysis_detail(request, analysis_id: str):
    if request.method == "OPTIONS":
        return _ok({"ok": True})
    if request.method != "GET":
        return _cors(HttpResponseNotAllowed(["GET", "OPTIONS"]))
    if not _auth_ok(request):
        return _bad("Unauthorized", 401)

    try:
        a = Analysis.objects.get(analysis_id=uuid.UUID(str(analysis_id)))
    except (ValueError, Analysis.DoesNotExist):
        return _bad("Not found", 404)

    followups = [
        {
            "position": fu.position,
            "question": fu.question_text,
            "why": fu.why,
            "answer": fu.answer_text or "",
        }
        for fu in a.followups.order_by("position")
    ]

    return _ok({
        "analysis_id": str(a.analysis_id),
        "status": a.status,
        "round": a.round,
        "input_text": a.input_text,
        "mood_score": a.mood_score,
        "questions": followups,  # altijd aanwezig (kan leeg zijn)
    })