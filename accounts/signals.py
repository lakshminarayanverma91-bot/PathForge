from allauth.account.models import EmailAddress
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver
from accounts.models import Profile


@receiver(social_account_added)
def save_user_data(sender, request, sociallogin, **kwargs):
    user = sociallogin.user

    # 🔹 Get email
    email = user.email

    # Save email in Allauth EmailAddress table
    if email:
        EmailAddress.objects.get_or_create(
            user=user,
            email=email,
            verified=True,
            primary=True
        )

    # Create or update Profile
    profile, created = Profile.objects.get_or_create(user=user)

    # 🔹 Save email in Profile
    if email:
        profile.email = email

    # 🔹 Optional: Save name (agar field hai)
    if hasattr(profile, 'name'):
        profile.name = user.get_full_name()

    profile.save()