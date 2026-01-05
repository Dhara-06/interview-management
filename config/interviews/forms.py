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
            "evaluation_criteria",
            "number_of_questions",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "required_skills": forms.Textarea(attrs={"rows": 2}),
            "responsibilities": forms.Textarea(attrs={"rows": 2}),
            "evaluation_criteria": forms.Textarea(attrs={"rows": 3, "placeholder": "Describe rubric or scoring criteria (e.g. correctness 50%, style 30%, clarity 20%)"}),
        }
