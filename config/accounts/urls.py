# accounts/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("register/", views.register, name="register"),
    path("", views.login_view, name="login"),
    path("hr/dashboard/", views.hr_dashboard, name="hr_dashboard"),
    path("candidate/dashboard/", views.candidate_dashboard, name="candidate_dashboard"),
    path("logout/", views.logout_view, name="logout"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
