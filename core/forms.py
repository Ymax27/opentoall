from django import forms


class SupportForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        label="Nom",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "name",
                "class": (
                    "w-full rounded-xl border border-outline-variant/60 "
                    "bg-surface-container-low px-4 py-3 text-on-surface "
                    "outline-none focus:ring-2 focus:ring-primary"
                ),
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "class": (
                    "w-full rounded-xl border border-outline-variant/60 "
                    "bg-surface-container-low px-4 py-3 text-on-surface "
                    "outline-none focus:ring-2 focus:ring-primary"
                ),
            }
        ),
    )
    message = forms.CharField(
        max_length=5000,
        label="Message",
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "class": (
                    "w-full rounded-xl border border-outline-variant/60 "
                    "bg-surface-container-low px-4 py-3 text-on-surface "
                    "outline-none focus:ring-2 focus:ring-primary resize-y"
                ),
            }
        ),
    )
    # Honeypot — leave empty. Bots that fill it are treated as a silent success.
    website = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "tabindex": "-1",
                "autocomplete": "off",
                "class": "hidden",
                "aria-hidden": "true",
            }
        ),
    )
