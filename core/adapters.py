"""Custom django-allauth adapters for seamless GitHub login."""

from __future__ import annotations

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Skip the ugly /accounts/3rdparty/signup/ step whenever possible.

    That page appears mainly when GitHub's email already exists on another
    Django user (e.g. the bootstrap admin). In that case we connect the
    social account instead of asking for a second signup form.
    """

    def is_auto_signup_allowed(self, request, sociallogin) -> bool:
        return True

    def pre_social_login(self, request, sociallogin) -> None:
        if sociallogin.is_existing:
            return

        User = get_user_model()
        emails: list[str] = []
        for address in sociallogin.email_addresses:
            if address.email:
                emails.append(address.email)
        if sociallogin.user and getattr(sociallogin.user, "email", None):
            emails.append(sociallogin.user.email)

        for email in emails:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                continue
            except User.MultipleObjectsReturned:
                user = User.objects.filter(email__iexact=email).order_by("id").first()
                if not user:
                    continue
            sociallogin.connect(request, user)
            return
