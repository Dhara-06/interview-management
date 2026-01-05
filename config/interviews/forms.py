from django import forms
from .models import Interview


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = [
            "title",
            "description",
            "required_skills",
            "responsibilities",
            "number_of_questions",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "required_skills": forms.Textarea(attrs={"rows": 2}),
            "responsibilities": forms.Textarea(attrs={"rows": 2}),
        }
