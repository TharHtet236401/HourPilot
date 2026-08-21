from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Workplace


@login_required
def workplace_list(request):
    try:
        workplaces = Workplace.objects.filter(
            user=request.user,
        ).order_by("-created_at")

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
