from django.urls import path

from . import views

urlpatterns = [
    path("", views.team_list, name="team_list"),
    path("add/", views.member_form, name="member_add"),
    path("<int:pk>/edit/", views.member_form, name="member_edit"),
    path("<int:pk>/toggle/", views.member_toggle_active, name="member_toggle"),
]
