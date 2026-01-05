from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from interviews.models import Interview
from .forms import RegisterForm
from .models import Profile


# =========================
# REGISTER VIEW
# =========================
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            role = form.cleaned_data["role"]

            # Ensure a single Profile exists and set the chosen role.
            # Use update_or_create to avoid IntegrityError when signals
            # or other code already created the Profile.
            Profile.objects.update_or_create(
                user=user,
                defaults={"role": role},
            )

            # Auto login
            login(request, user)
            messages.success(request, "Registration successful. Redirecting...")

            # Redirect based on role
            if role == "HR":
                return redirect("hr_dashboard")
            else:
                return redirect("candidate_dashboard")
        else:
            # Provide feedback for debugging / user visibility
            messages.error(request, "There was a problem with your registration.")
            # Attach form errors to messages for easier debugging in browser
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f"{field}: {e}")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


# =========================
# LOGIN VIEW
# =========================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ✅ SAFE profile access
            profile = Profile.objects.get(user=user)

            if profile.role == "HR":
                return redirect("hr_dashboard")
            else:
                return redirect("candidate_dashboard")

        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


# =========================
# DASHBOARD REDIRECT
# =========================
@login_required
def dashboard_redirect(request):
    profile = Profile.objects.get(user=request.user)

    if profile.role == "HR":
        return redirect("hr_dashboard")
    return redirect("candidate_dashboard")


# =========================
# HR DASHBOARD
# =========================
@login_required
def hr_dashboard(request):
    interviews = Interview.objects.filter(created_by=request.user)
    return render(request, "accounts/hr_dashboard.html", {
        "interviews": interviews
    })


# =========================
# CANDIDATE DASHBOARD
# =========================
@login_required
def candidate_dashboard(request):
    interviews = Interview.objects.all()
    return render(request, "accounts/candidate_dashboard.html", {
        "interviews": interviews
    })


# =========================
# LOGOUT
# =========================
def logout_view(request):
    logout(request)
    return redirect("login")
