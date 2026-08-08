"""Keep a Profile in sync with Django users and GitHub social accounts."""

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User as DjangoUser
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=DjangoUser)
def ensure_profile_exists(sender, instance, created, **kwargs):
    """Every user (including superusers) gets a Profile."""
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={"github_username": instance.username},
        )


@receiver(post_save, sender=SocialAccount)
def sync_profile_from_github(sender, instance, created, **kwargs):
    """Enrich the profile with data coming from the GitHub OAuth payload."""
    if instance.provider != "github":
        return

    data = instance.extra_data or {}
    profile, _ = Profile.objects.get_or_create(user=instance.user)

    profile.github_username = data.get("login") or profile.github_username
    profile.avatar_url = data.get("avatar_url") or profile.avatar_url
    profile.bio = data.get("bio") or profile.bio
    if data.get("location") and not profile.country:
        profile.country = data.get("location")
    profile.save()
