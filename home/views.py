from django.shortcuts import render

def home(request):
    return render(request, "home/index.html")

def about(request):
    return render(request, "home/about.html")

def contact(request):
    return render(request, "home/contact.html")

def privacy(request):
    return render(request, "home/privacy-policy.html")

def terms(request):
    return render(request, "home/terms-of-use.html")
