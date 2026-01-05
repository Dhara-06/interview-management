from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class Interview(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.TextField()
    responsibilities = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    number_of_questions = models.IntegerField(default=5)  # ✅ NEW
    # Allows HR to specify evaluation criteria (rubric, scoring notes)
    evaluation_criteria = models.TextField(blank=True)

    def __str__(self):
        return self.title


class InterviewAnswer(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    question_number = models.IntegerField()  # ✅ NEW
    question = models.TextField()
    answer = models.TextField()

    ai_feedback = models.TextField(blank=True)
    ai_score = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.username} - {self.interview.title} (Q{self.question_number})"


class InterviewResult(models.Model):
    """Overall interview evaluation stored when the AI/tool completes evaluation."""
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    overall_score = models.IntegerField(null=True, blank=True)
    overall_feedback = models.TextField(blank=True)

    # Keep raw JSON payload from the tool for auditing/debugging
    raw_payload = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result: {self.candidate.username} - {self.interview.title} ({self.overall_score})"


class AskedQuestion(models.Model):
    """Record of a question shown to a candidate for a specific interview.

    This helps ensure questions aren't repeated across sessions by the same candidate.
    """
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question_text = models.TextField()
    displayed_at = models.DateTimeField(auto_now_add=True)
    answered = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["interview", "candidate"]) ]

    def __str__(self):
        return f"Asked: {self.candidate.username} - {self.interview.title} ({self.displayed_at})"
