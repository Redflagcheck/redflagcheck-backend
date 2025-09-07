# backend/redflagcheck/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User



STATUS_CHOICES = [
    ("intake", "Intake verzameld"),
    ("followup_pending", "Follow-up gevraagd"),
    ("ready", "Klaar voor analyse"),
]


class Analysis(models.Model):
    analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wp_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    # Intake en andere metadata
    data = models.JSONField(default=dict, blank=True)

    # Nieuwe velden voor stap 5
    followup_questions = models.JSONField(default=list, blank=True)
    followup_answers = models.JSONField(default=dict, blank=True)

    ocr_text = models.TextField(blank=True, default="")
    ocr_corrected_text = models.TextField(blank=True, default="")

    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default="intake",
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Analysis {self.analysis_id}"