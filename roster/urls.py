from django.urls import path

from . import views

urlpatterns = [
    path("", views.roster_week, name="roster_week"),
    path("set/", views.set_shift, name="roster_set_shift"),
    path("copy-prev/", views.copy_prev_week, name="roster_copy_prev"),
    path("shifts/", views.shift_list, name="shift_list"),
    path("shifts/add/", views.shift_form, name="shift_add"),
    path("shifts/<int:pk>/edit/", views.shift_form, name="shift_edit"),
    path("shifts/<int:pk>/delete/", views.shift_delete, name="shift_delete"),
]
