# campuspathAI/urls.py
# ============================================================
# All URL routes for CampusPath AI
# ============================================================

from django.urls import path
from . import views

app_name = 'campuspath'

urlpatterns = [

    # ── Main page (shows form + roadmap) ─────────────────────
    # URL: /campuspath/
    path('', views.campuspath_home, name='home'),

    # ── View a specific roadmap by ID ────────────────────────
    # URL: /campuspath/roadmap/5/
    path('roadmap/<int:roadmap_id>/', views.roadmap_detail, name='roadmap_detail'),

    # ── API: Generate a new roadmap via Gemini ───────────────
    # URL: /campuspath/api/generate/   POST
    path('api/generate/', views.generate_roadmap, name='generate_roadmap'),

    # ── API: Connect GitHub profile ──────────────────────────
    # URL: /campuspath/api/github/connect/   POST
    path('api/github/connect/', views.connect_github, name='connect_github'),

    # ── API: Get roadmap as JSON (for frontend rendering) ────
    # URL: /campuspath/api/roadmap/5/   GET
    path('api/roadmap/<int:roadmap_id>/', views.get_roadmap_json, name='roadmap_json'),

    # ── API: Update/regenerate an existing roadmap ───────────
    # URL: /campuspath/api/roadmap/5/update/   POST
    path('api/roadmap/<int:roadmap_id>/update/', views.update_roadmap, name='update_roadmap'),

    # ── API: Toggle a week complete/incomplete ───────────────
    # URL: /campuspath/api/week/12/toggle/   POST
    path('api/week/<int:week_id>/toggle/', views.toggle_week_complete, name='toggle_week'),

    # ── API: Toggle a task done/undone ───────────────────────
    # URL: /campuspath/api/task/34/toggle/   POST
    path('api/task/<int:task_id>/toggle/', views.toggle_task_done, name='toggle_task'),

    # ── API: Save progress manually ──────────────────────────
    # URL: /campuspath/api/save/   POST
    path('api/save/', views.save_progress, name='save_progress'),

]