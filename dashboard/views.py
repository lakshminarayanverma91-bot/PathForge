from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import Profile

@login_required
def dashboard(request):
    # Use Profile data when available, otherwise fall back to auth User
    # (e.g. admin/superuser accounts without a Profile row).
    dashboard_user = Profile.objects.filter(pk=request.user.pk).first() or request.user
    data = {
        "all_users": [dashboard_user]
    }
    return render(request, "dashboard/dashboard.html", data)

@login_required
def profile(request):
    # Keep data source consistent with dashboard: Profile when available,
    # otherwise fall back to auth User (e.g. admin without Profile row).
    profile_user = Profile.objects.filter(pk=request.user.pk).first() or request.user

    data = {
        "all_users": [profile_user],
    }

    return render(request, "dashboard/profile.html", data)

@login_required
def crackAI(request):
    return render(request, "dashboard/crackAI.html")

@login_required
def ventureIQ(request):
    return render(request, "dashboard/ventureIQ.html")

@login_required
def campuspathAI(request):
    return render(request, "dashboard/campuspathAI.html")

@login_required
def mindmateAI(request):
    return render(request, "dashboard/mindmateAI.html")

@login_required
def feedback(request):
    return render(request, "dashboard/feedback.html")
