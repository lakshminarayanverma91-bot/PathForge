from django.db import models

class Review(models.Model):
    stars = models.CharField(max_length=5)
    description = models.CharField(max_length=800, null=True, blank=True)
    name = models.CharField(max_length=20)
    course = models.CharField(max_length=15)
    college = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
