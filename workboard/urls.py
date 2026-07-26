from django.urls import path

from . import views

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("add/", views.task_form, name="task_add"),
    path("<int:pk>/edit/", views.task_form, name="task_edit"),
    path("<int:pk>/status/", views.task_set_status, name="task_set_status"),
    path("<int:pk>/delete/", views.task_delete, name="task_delete"),
]
