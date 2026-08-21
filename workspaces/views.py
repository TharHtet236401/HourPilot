from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import WorkplaceForm
from .models import Workplace


def _user_workplaces(user):
    return Workplace.objects.filter(user=user).order_by("-created_at")


@login_required
def workplace_list(request):
    try:
        workplaces = _user_workplaces(request.user)
        return render(
            request,
            "workspaces/list.html",
            {"workplaces": workplaces},
        )
    except Exception:
        messages.error(request, "Could not load your workspaces.")
        return render(
            request,
            "workspaces/list.html",
            {"workplaces": []},
        )


@login_required
def workplace_create(request):
    try:
        if request.method == "POST":
            form = WorkplaceForm(request.POST)
            if form.is_valid():
                workplace = form.save(commit=False)
                workplace.user = request.user
                workplace.save()
                return render(
                    request,
                    "workspaces/partials/create_success.html",
                    {"workplaces": _user_workplaces(request.user)},
                )
        else:
            form = WorkplaceForm()

        return render(
            request,
            "workspaces/partials/modal_form.html",
            {"form": form},
        )
    except Exception:
        form = WorkplaceForm(request.POST or None)
        return render(
            request,
            "workspaces/partials/modal_form.html",
            {
                "form": form,
                "error": "Could not save this workplace.",
            },
        )
