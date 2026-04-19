"""
urls.py — CrackAI
"""
from django.urls import path
from . import views

app_name = 'crackai'

urlpatterns = [
    path('start/', views.start_session, name='start_session'),
    path('answer/<int:question_id>/', views.submit_answer, name='submit_answer'),
    path('end/<uuid:session_id>/', views.end_session, name='end_session'),
    path('history/', views.session_history, name='session_history'),
    path('session/<uuid:session_id>/', views.session_detail, name='session_detail'),
    path('abandon/<uuid:session_id>/', views.abandon_session, name='abandon_session'),
]