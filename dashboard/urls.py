from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("crackAI/", views.crackAI, name="crackAI"),
    path("ventureIQ/", views.ventureIQ, name="ventureIQ"),
    path("campuspathAI/", views.campuspathAI, name="campuspathAI"),
    path("mindmateAI/", views.mindmateAI, name="mindmateAI"),
    path("feedback/", views.feedback, name="feedback"),
    path("profile/", views.profile, name="profile"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("delete-profile/", views.delete_profile, name="delete_profile"),
]
