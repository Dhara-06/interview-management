from xml.etree.ElementInclude import include
from django.urls import path
from . import views

urlpatterns = [
    path("<int:interview_id>/", views.interview_detail, name="interview_detail"),
    path("<int:interview_id>/start/", views.interview_session, name="interview_session"),
    path("hr/create/", views.hr_create_interview, name="hr_create_interview"),
    path("hr/edit/<int:interview_id>/", views.hr_edit_interview, name="hr_edit_interview"),
    path("hr/answers/", views.hr_view_answers, name="hr_view_answers"),
    path(
        "hr/answers/delete/<int:answer_id>/",
        views.delete_answer,
        name="delete_answer"
    ),
]
