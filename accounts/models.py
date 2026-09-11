from django.db import models
from django.contrib.auth.models import User

class Profile(User):
    phone_no = models.CharField(max_length= 13, blank=True, default="")
    linkedin = models.URLField(null= True, blank= True)
    github = models.URLField(null= True, blank= True)
    role = models.CharField(max_length= 30, null= True, blank= True)
    about = models.CharField(max_length= 500, null= True, blank= True)
    image = models.ImageField(null= True, blank= True, upload_to="images/")
    cover_image = models.ImageField(null= True, blank= True, upload_to="images/")
    university = models.CharField(max_length=20, null= True, blank= True)

    GENDER_CHOICE = (
        ("Male", "male"),
        ("Female", "female"),
        ("Prefer not to say", "Prefer not to say")
    )

    gender = models.CharField(max_length=20, choices= GENDER_CHOICE, null= True, blank= True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
