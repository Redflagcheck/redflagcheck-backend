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
    feedback_rewards = models.IntegerField(default=0)  # aantal extra analyses verdiend via feedback
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
    reason_q1 = models.TextField(null=True, blank=True)
    answer1 = models.TextField(null=True, blank=True)
    question2 = models.TextField(null=True, blank=True)
    reason_q2 = models.TextField(null=True, blank=True)
    answer2 = models.TextField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    gpt_result_html = models.TextField(null=True, blank=True)
    is_charged = models.BooleanField(default=False) #is het resultaat getoond?
    charged_at = models.DateTimeField(null=True, blank=True) #wanneer is het resultaat getoond
    satisfaction_score = models.IntegerField(null=True, blank=True)  # 1 t/m 5
    nps_score = models.IntegerField(null=True, blank=True)          # 0 t/m 10
    user_feedback = models.TextField(null=True, blank=True)         # open tekst
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis {self.analysis_id} — {self.user_email}"

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    old_email = models.EmailField()
    new_email = models.EmailField(null=True, blank=True)
    credits = models.IntegerField()
    balance_before = models.IntegerField(null=True, blank=True)
    restored = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.payment_id} — {self.old_email} (+{self.credits} credits)"