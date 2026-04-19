# dashboard/urls.py mein add karo

from django.urls import path
from . import views

urlpatterns = [

    # ... tumhari existing urls ...

    path('ventureiq/', views.ventureIQ, name='ventureIQ'),
    path('ventureiq/analyze/', views.ventureiq_analyze, name='ventureiq_analyze'),
    path('ventureiq/analysis/<uuid:pk>/', views.ventureiq_load, name='ventureiq_load'),
    path('ventureiq/analysis/<uuid:pk>/delete/', views.ventureiq_delete, name='ventureiq_delete'),
    path('ventureiq/analysis/<uuid:pk>/save/', views.ventureiq_toggle_save, name='ventureiq_save'),
]