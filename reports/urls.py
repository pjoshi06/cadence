from django.urls import path

from . import views

urlpatterns = [
    path("", views.report_home, name="report_home"),
    path("templates/", views.template_list, name="template_list"),
    path("templates/<int:pk>/delete/", views.template_delete, name="template_delete"),
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/sample-csv/", views.sample_csv, name="sample_csv"),
]
