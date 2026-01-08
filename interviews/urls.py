from xml.etree.ElementInclude import include
from django.urls import path
from . import views

urlpatterns = [
    path("<int:interview_id>/", views.interview_detail, name="interview_detail"),
    path("<int:interview_id>/start/", views.interview_session, name="interview_session"),
    path("hr/create/", views.hr_create_interview, name="hr_create_interview"),
    path("hr/edit/<int:interview_id>/", views.hr_edit_interview, name="hr_edit_interview"),
    path("hr/delete/<int:interview_id>/", views.hr_delete_interview, name="hr_delete_interview"),
    path("<int:interview_id>/chat/", views.ai_chat, name="ai_chat"),
    path("<int:interview_id>/callback/", views.api_callback, name="api_callback"),
    path("hr/results/", views.hr_results, name="hr_results"),
    path("hr/results/<int:result_id>/", views.hr_view_result, name="hr_view_result"),
    path("hr/results/<int:result_id>/delete/", views.hr_delete_result, name="hr_delete_result"),
    path("hr/answer/<int:answer_id>/delete/", views.delete_answer, name="delete_answer"),
    path("hr/results/<int:interview_id>/candidate/<int:candidate_id>/", views.hr_view_result_by_candidate, name="hr_view_result_by_candidate"),
    # Candidate answers listing removed (use Interview Results instead)
]
