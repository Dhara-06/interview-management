from django import forms
from django.contrib.auth.models import User
from .models import Profile

class RegisterForm(forms.ModelForm):
    ROLE_CHOICES = (
        ("HR", "HR"),
        ("CANDIDATE", "Candidate"),
    )

    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                role=self.cleaned_data["role"]
            )

        return user
