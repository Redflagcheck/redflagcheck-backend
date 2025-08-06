from django.db import models


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    name = models.TextField(null=True, blank=True)
    password_hash = models.TextField(null=True, blank=True)
    token = models.CharField(max_length=255, unique=True)
    balance = models.IntegerField(default=0)
    email_verified = models.BooleanField(default=False)
    magic_code = models.TextField(null=True, blank=True)
    magic_code_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


class Analysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_email = models.TextField(null=True, blank=True, db_index=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField()
    context = models.TextField(null=True, blank=True)
    screenshot_url = models.TextField(null=True, blank=True)
    ocr = models.TextField(null=True, blank=True)
    question1 = models.TextField(null=True, blank=True)
    answer1 = models.TextField(null=True, blank=True)
    question2 = models.TextField(null=True, blank=True)
    answer2 = models.TextField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    gpt_result_html = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis {self.analysis_id} — {self.user_email}"