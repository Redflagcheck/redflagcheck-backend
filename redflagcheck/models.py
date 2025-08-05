from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    balance = models.IntegerField(default=0)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email or f"User {self.user_id}"

class Analysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    context = models.TextField(blank=True, null=True)
    screenshot_url = models.URLField(blank=True, null=True)
    result = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis {self.analysis_id}"
