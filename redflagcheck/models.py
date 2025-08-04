from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    token = models.CharField(max_length=255, null=True, blank=True)
    credit_balance = models.IntegerField(default=0)
    email_verified = models.BooleanField(default=False)
    magic_code = models.CharField(max_length=255, null=True, blank=True)
    magic_code_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'redflagcheck_users'
        managed = False
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email or f"User {self.user_id}"

class Analysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(
        User,
        db_column='user_id',
        on_delete=models.DO_NOTHING
    )
    parent_id = models.IntegerField(null=True, blank=True)
    message = models.TextField()
    context = models.TextField(null=True, blank=True)
    screenshot = models.TextField(null=True, blank=True)
    ocr = models.TextField(null=True, blank=True)
    question1 = models.TextField(null=True, blank=True)
    answer1 = models.TextField(null=True, blank=True)
    question2 = models.TextField(null=True, blank=True)
    answer2 = models.TextField(null=True, blank=True)
    gpt_result = models.TextField(null=True, blank=True)
    gpt_result_html = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'redflagcheck_analyses'
        managed = False
        verbose_name_plural = "Analyses"

    def __str__(self):
        return f"Analysis {self.analysis_id}"
