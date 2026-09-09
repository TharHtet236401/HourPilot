from allauth.account.models import EmailAddress
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import AccountPasswordForm, EmailChangeForm, PreferencesForm
from .prefs import get_profile


def _account_forms(request, profile, data=None, active=None):
    bound = data if data is not None else None
    return {
        "preferences_form": PreferencesForm(
            bound if active == "preferences" else None,
            instance=profile,
        ),
        "email_form": EmailChangeForm(
            request.user,
            bound if active == "email" else None,
        ),
        "password_form": AccountPasswordForm(
            request.user,
            bound if active == "password" else None,
        ),
        "active_form": active,
    }


@login_required
def account(request):
    try:
        profile = get_profile(request.user)
        if request.method != "POST":
            return render(
                request,
                "account/manage.html",
                _account_forms(request, profile),
            )

        which = request.POST.get("form")
        if which == "preferences":
            form = PreferencesForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Preferences saved.")
                return redirect("account")
            context = _account_forms(request, profile, data=request.POST, active="preferences")
            context["preferences_form"] = form
            return render(request, "account/manage.html", context)

        if which == "email":
            form = EmailChangeForm(request.user, request.POST)
            if form.is_valid():
                _save_email(request.user, form.cleaned_data["email"])
                messages.success(request, "Email updated.")
                return redirect("account")
            context = _account_forms(request, profile, data=request.POST, active="email")
            context["email_form"] = form
            return render(request, "account/manage.html", context)

        if which == "password":
            form = AccountPasswordForm(request.user, request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password updated.")
                return redirect("account")
            context = _account_forms(request, profile, data=request.POST, active="password")
            context["password_form"] = form
            return render(request, "account/manage.html", context)

        messages.error(request, "Could not save those account details.")
        return redirect("account")
    except Exception:
        messages.error(request, "Could not update your account.")
        profile = get_profile(request.user)
        return render(
            request,
            "account/manage.html",
            _account_forms(request, profile),
        )


def _save_email(user, email):
    old_email = user.email
    with transaction.atomic():
        user.email = email
        update_fields = ["email"]
        if user.username == old_email:
            user.username = email
            update_fields.append("username")
        user.save(update_fields=update_fields)
        EmailAddress.objects.filter(user=user).exclude(email__iexact=email).delete()
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"primary": True, "verified": True},
        )
