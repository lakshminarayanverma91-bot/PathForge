from django.urls import path
from . import views

urlpatterns = [

    # ... tumhari existing urls ...

    path('', views.ventureIQ, name='ventureIQ'),
    path('analyze/', views.ventureiq_analyze, name='ventureiq_analyze'),
    path('analysis/<uuid:pk>/', views.ventureiq_load, name='ventureiq_load'),
    path('analysis/<uuid:pk>/delete/', views.ventureiq_delete, name='ventureiq_delete'),
    path('analysis/<uuid:pk>/save/', views.ventureiq_toggle_save, name='ventureiq_save'),
]