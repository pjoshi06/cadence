from django.urls import path

from . import views

urlpatterns = [
    path("jobs/", views.job_board, name="job_board"),
    path("jobs/set/", views.run_set, name="job_run_set"),
    path("jobs/mark-rest/", views.mark_rest_success, name="job_mark_rest"),
    path("jobs/import/", views.run_import, name="job_run_import"),
    path("jobs/sample-csv/", views.sample_run_csv, name="job_sample_csv"),
    path("jobs/master/", views.job_master, name="job_master"),
    path("jobs/master/add/", views.job_form, name="job_add"),
    path("jobs/master/<int:pk>/edit/", views.job_form, name="job_edit"),
    path("jobs/master/<int:pk>/toggle/", views.job_toggle, name="job_toggle"),
]
