from django import forms
from django.contrib.auth.models import User
from .models import Profile

class RegisterForm(forms.ModelForm):
    ROLE_CHOICES = (
        ("HR", "HR"),
        ("CANDIDATE", "Candidate"),
    )

    password = forms.CharField(widget=forms.PasswordInput)
    full_name = forms.CharField(required=False)
    contact_number = forms.CharField(required=False)
    resume = forms.FileField(required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
        return user


        return user
