# backend/redflagcheck/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User

class Analysis(models.Model):
    analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wp_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    # Alle intake/vragen/antwoorden/resultaten/feedback in één JSON
    data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Analysis {self.analysis_id}"
