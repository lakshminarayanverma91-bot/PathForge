from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib import auth
from .models import Profile

def login(request):

    if request.method == "POST":
        username = request.POST.get("username") or request.POST.get("email")
        password = request.POST.get("password")

        user = auth.authenticate(request, username = username, password = password)

        if user is not None:
            auth.login(request, user)
            return redirect("dashboard")
        
        else:
            messages.error(request, "User not found")

    return render(request, "accounts/login.html")

def register(request):

    if request.method == "POST":

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone_no = request.POST.get("mobile")
        university = request.POST.get("college")
        password = request.POST.get("password1")
        confirm_password = request.POST.get("password2")

        if password == confirm_password:

            profile = Profile(
                first_name = first_name,
                last_name = last_name,
                username = username,
                email = email,
                phone_no = phone_no,
                university = university
            )

            profile.set_password(password)
            profile.save()

            return redirect("login")
        
        else:
            messages.error(request, "Passwords do not match")

    return render(request, "accounts/register.html")

def logout(request):
    auth.logout(request)
    return redirect("home")