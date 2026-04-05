from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Review

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

def reviews(request):
    reviews = list(Review.objects.order_by("-id"))

    total_reviews = len(reviews)
    stars_total = 0
    college_set = set()

    for review in reviews:
        try:
            stars_value = int(str(review.stars).strip())
        except (TypeError, ValueError):
            stars_value = 0

        stars_value = max(0, min(5, stars_value))
        review.star_value = stars_value
        review.star_display = "★" * stars_value + "☆" * (5 - stars_value)

        stars_total += stars_value

        college_name = (review.college or "").strip().lower()
        if college_name:
            college_set.add(college_name)

    avg_rating = round(stars_total / total_reviews, 1) if total_reviews else 0
    full_stars = int(avg_rating)
    half_star = (avg_rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)
    overview_stars = "★" * full_stars + ("⯨" if half_star else "") + "☆" * max(0, empty_stars)

    distribution = []
    for star in [5, 4, 3, 2, 1]:
        count = sum(1 for review in reviews if review.star_value == star)
        pct = round((count / total_reviews) * 100) if total_reviews else 0
        distribution.append(
            {
                "stars": star,
                "count": count,
                "pct": pct,
                "display": "★" * star,
            }
        )

    data = {
        "reviews": reviews,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
        "overview_stars": overview_stars,
        "distribution": distribution,
        "college_count": len(college_set),
    }

    return render(request, "home/reviews.html", data)

@login_required
def add_review(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()[:20]
        course = request.POST.get("course", "").strip()[:15]
        college = request.POST.get("college", "").strip()[:20]
        description = request.POST.get("description", "").strip()[:800]

        try:
            stars_value = int(request.POST.get("stars", "0"))
        except (TypeError, ValueError):
            stars_value = 0

        stars_value = max(1, min(5, stars_value))

        if name and course and college and description:
            Review.objects.create(
                stars=str(stars_value),
                description=description,
                name=name,
                course=course,
                college=college,
            )
            return redirect("reviews")

    return render(request, "home/add_review.html")
