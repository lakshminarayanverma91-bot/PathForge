from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection, IntegrityError
from accounts.models import Profile
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth import update_session_auth_hash


def _dashboard_context(request, extra=None):
    context = {
        "user": request.user,
        "profile": Profile.objects.filter(pk=request.user.pk).first(),
    }
    if extra:
        context.update(extra)
    return context

@login_required
def dashboard(request):

    if not request.user.has_usable_password():
        return redirect('set_password')

    return render(request, "dashboard/dashboard.html", _dashboard_context(request))

@login_required
def profile(request):
    return render(request, "dashboard/profile.html", _dashboard_context(request))

@login_required
def crackAI(request):
    return render(request, "dashboard/crackAI.html", _dashboard_context(request))

@login_required
def ventureIQ(request):
    return render(request, "dashboard/ventureIQ.html", _dashboard_context(request))

@login_required
def campuspathAI(request):
    return render(request, "dashboard/campuspathAI.html", _dashboard_context(request))

@login_required
def mindmateAI(request):
    return render(request, "dashboard/mindmateAI.html", _dashboard_context(request))

@login_required
def feedback(request):

    if request.method == "POST":

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        topic = request.POST.get("topic")
        priority = request.POST.get("priority")
        message = request.POST.get("message")

        full_message = f"""
        🚀 New Contact Submission

        👤 Name: {first_name} {last_name}
        📧 Email: {email}

        📌 Topic: {topic}
        ⚡ Priority: {priority}

        💬 Message:
        {message}
        """

        email_message = EmailMessage(
            subject=f"[{topic}] New Message - {priority} Priority",
            body=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_RECEIVER_EMAIL],
            reply_to=[email]
        )

        email_message.send()

    return render(request, "dashboard/feedback.html", _dashboard_context(request))

@login_required
def edit_profile(request):

    profile = Profile.objects.filter(pk=request.user.pk).first()

    if request.method == "POST":

        # ===== USER FIELDS =====
        request.user.first_name = (request.POST.get("first_name") or "").strip()
        request.user.last_name = (request.POST.get("last_name") or "").strip()
        request.user.email = (request.POST.get("email") or "").strip()
        request.user.save()

        # Ensure every authenticated user has a Profile row.
        # Profile uses multi-table inheritance from User, so creating through ORM
        # for an existing User may try inserting auth_user again and fail.
        if not profile:
            table = Profile._meta.db_table
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        INSERT INTO {table}
                        (user_ptr_id, phone_no, linkedin, github, role, about, image, cover_image, university, gender)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [request.user.pk, "", None, None, None, None, None, None, None, None],
                    )
            except IntegrityError:
                # Row may have been created in another request; continue safely.
                pass

        # Reload profile after user save to avoid stale inherited values.
        profile = Profile.objects.get(pk=request.user.pk)

        # ===== PROFILE FIELDS =====
        profile.phone_no = ((request.POST.get("phone_no") or "").strip())[:13]
        profile.github = (request.POST.get("github") or "").strip() or None
        profile.linkedin = (request.POST.get("linkedin") or "").strip() or None

        gender = (request.POST.get("gender") or "").strip()
        valid_gender = {choice[0] for choice in Profile.GENDER_CHOICE}
        profile.gender = gender if gender in valid_gender else None

        profile.university = (request.POST.get("university") or "").strip() or None
        profile.role = (request.POST.get("role") or "").strip() or None
        profile.about = (request.POST.get("about") or "").strip() or None

        # remove image first if requested
        update_fields = ["phone_no", "github", "linkedin", "gender", "university", "role", "about"]

        if request.POST.get("remove_image") == "true":
            if profile.image:
                profile.image.delete(save=False)
            profile.image = None
            update_fields.append("image")

        # image upload
        if request.FILES.get("image"):
            profile.image = request.FILES.get("image")
            if "image" not in update_fields:
                update_fields.append("image")

        profile.save(update_fields=update_fields)

        # ===== PASSWORD CHANGE (basic) =====
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password1")
        confirm_password = request.POST.get("new_password2")

        if current_password and new_password and confirm_password:
            if request.user.check_password(current_password) and new_password == confirm_password:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)

        return redirect("profile")

    return render(request, "dashboard/edit_profile.html", _dashboard_context(request, {
        "profile": profile
    }))

@login_required
def set_password(request):

    if request.user.has_usable_password():
        return redirect("dashboard")

    if request.method == "POST":
        password = request.POST.get("password")

        if not password:
            return redirect("set_password")

        user = request.user
        user.set_password(password)
        user.save()

        update_session_auth_hash(request, user)

        return redirect("dashboard")

    return render(request, "accounts/set_password.html")

@login_required
def delete_profile(request):
    if request.method != "POST":
        return redirect("profile")

    user = request.user

    # Extra safety: avoid removing the only admin account from dashboard forms.
    if user.is_superuser:
        messages.error(request, "Superuser account cannot be deleted from this page.")
        return redirect("profile")

    if request.POST.get("confirm_delete") != "yes":
        messages.error(request, "Delete confirmation missing.")
        return redirect("profile")

    password = (request.POST.get("password") or request.POST.get("current_password") or "").strip()
    if not password or not user.check_password(password):
        messages.error(request, "Please enter your current password to delete account.")
        return redirect("profile")

    logout(request)
    user.delete()
    return redirect("login")
