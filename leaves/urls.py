from django.urls import path

from . import views

urlpatterns = [
    path("", views.leave_list, name="leave_list"),
    path("apply/", views.leave_apply, name="leave_apply"),
    path("<int:pk>/<str:decision>/", views.leave_decide, name="leave_decide"),
    path("<int:pk>/cancel/", views.leave_cancel, name="leave_cancel"),
]
