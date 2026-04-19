from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('optimus/', admin.site.urls),
    path("", include("home.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("ventureIQ/", include("ventureIQ.urls")),
    path("campuspathAI/", include("campuspathAI.urls")),
    path("crackAI/", include("crackAI.urls"))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)