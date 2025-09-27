import uuid
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.core.validators import MinValueValidator

# ---- Managers (soft delete) ----
class NotDeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


# ---- Choices ----
class AnalysisStatus(models.TextChoices):
    INTAKE = "intake", "Intake opgeslagen"
    QUESTIONS_READY = "questions_ready", "Vragen gegenereerd"
    ANSWERS_SAVED = "answers_saved", "Antwoorden opgeslagen"
    COMPLETED = "completed", "Afronding gereed"


class AuditSeverity(models.TextChoices):
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    ERROR = "error", "Error"


# ---- Models ----
class Analysis(models.Model):
    analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    wp_user_id = models.IntegerField(null=True, blank=True, db_index=True)
    email = models.EmailField(null=True, blank=True, db_index=True)
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Verwijzing naar de eerste/bovenliggende analyse."
    )
    round = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Ronde in casus (≥1).")

    input_text = models.TextField(help_text="Originele tekst van gebruiker (verplicht).")
    screenshot_url = models.CharField(max_length=512, null=True, blank=True)
    ocr_text = models.TextField(null=True, blank=True)

    mood_score = models.IntegerField(null=True, blank=True)
    context = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=120, null=True, blank=True)

    result_text = models.TextField(null=True, blank=True)
    result_html = models.TextField(null=True, blank=True)
    result_json = models.JSONField(null=True, blank=True)

    status = models.CharField(max_length=32, choices=AnalysisStatus.choices, default=AnalysisStatus.INTAKE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback_text = models.TextField(null=True, blank=True)
    rated_at = models.DateTimeField(null=True, blank=True)

    ip_address = models.CharField(max_length=45, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Managers
    objects = NotDeletedManager()      # standaard: filtert soft-deleted weg
    all_objects = models.Manager()     # inclusief soft-deleted

    class Meta:
        verbose_name = "Analysis"
        verbose_name_plural = "Analyses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["ip_address"]),     # optioneel maar handig voor throttling
            models.Index(fields=["deleted_at"]),     # optioneel voor housekeeping
        ]
        constraints = [
            # 1 rondenummer per casus (NB: meerdere NULL parent_id toegestaan per SQL-standaard)
            models.UniqueConstraint(fields=["parent", "round"], name="uniq_round_per_parent"),

            # round ≥ 1
            models.CheckConstraint(check=Q(round__gte=1), name="ck_round_gte_1"),

            # rating tussen 1..5 of NULL
            models.CheckConstraint(
                check=Q(rating__gte=1, rating__lte=5) | Q(rating__isnull=True),
                name="ck_rating_1_5_or_null",
            ),

            # mood_score (optioneel) tussen 1..5 of NULL
            models.CheckConstraint(
                check=Q(mood_score__gte=1, mood_score__lte=5) | Q(mood_score__isnull=True),
                name="ck_mood_1_5_or_null",
            ),
        ]

    def __str__(self):
        return f"Analysis({self.analysis_id}, r{self.round}, {self.status})"


class Followup(models.Model):
    """
    Eén verdiepingsvraag (GPT) + verplicht antwoord, gekoppeld aan een specifieke analyse/ronde.
    """
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name="followups")
    position = models.PositiveSmallIntegerField(help_text="Volgorde binnen de analyse (1,2,...)")

    question_text = models.TextField()
    why = models.TextField()
    answer_text = models.TextField(help_text="Antwoord van de gebruiker (verplicht).")
    model_version = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["analysis", "position", "created_at"]
        constraints = [
            models.UniqueConstraint(fields=["analysis", "position"], name="uniq_followup_position_per_analysis"),
        ]
        indexes = [
            models.Index(fields=["created_at"]),  # optioneel: housekeeping
            # NB: (analysis, position) is al gedekt door de UNIQUE-constraint
        ]


    def __str__(self):
        # was: return f"Followup(A={self.analysis_id}, pos={self.position})"
        return f"Followup(A={self.analysis.analysis_id}, pos={self.position})"

class AuditEvent(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    wp_user_id = models.IntegerField(null=True, blank=True, db_index=True)
    type = models.CharField(max_length=64, db_index=True)
    severity = models.CharField(max_length=16, choices=AuditSeverity.choices, default=AuditSeverity.INFO, db_index=True)
    subject_ref = models.CharField(max_length=128, null=True, blank=True)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    ip_address = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["type", "severity"]),
            models.Index(fields=["wp_user_id", "created_at"]),  # optioneel: tijdlijn per gebruiker
            models.Index(fields=["subject_ref"]),               # optioneel: zoeken op analysis_id/token
            models.Index(fields=["ip_address"]),                # optioneel: misbruikpatronen
        ]

    def __str__(self):
        return f"Audit({self.type}/{self.severity})"