from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, render

from config.pagination import (
    WORKPLACE_PAGE_SIZE,
    list_page_url,
    page_number_from_request,
    paginate,
)

from .forms import WorkplaceForm
from .models import Workplace


def _user_workplaces(user):
    return (
        Workplace.objects.filter(user=user)
        .annotate(shift_count=Count("shifts"))
        .order_by("-created_at")
    )


def _workplace_list_context(request, page=None):
    page_obj = paginate(
        _user_workplaces(request.user),
        page if page is not None else page_number_from_request(request),
        WORKPLACE_PAGE_SIZE,
    )
    return {
        "workplaces": page_obj.object_list,
        "page_obj": page_obj,
        "page_url_name": "workplace_list",
        "list_target": "#workplace-list",
    }


def _workplace_form_success(request, message, page=None):
    context = _workplace_list_context(request, page=page)
    context["message"] = message
    response = render(request, "workspaces/partials/list_refresh.html", context)
    response["HX-Push-Url"] = list_page_url(
        "workplace_list", context["page_obj"].number
    )
    return response


@login_required
def workplace_list(request):
    try:
        context = _workplace_list_context(request)
        template = (
            "workspaces/partials/list.html"
            if request.headers.get("HX-Request")
            else "workspaces/list.html"
        )
        return render(request, template, context)
    except Exception:
        messages.error(request, "Could not load your workspaces.")
        template = (
            "workspaces/partials/list.html"
            if request.headers.get("HX-Request")
            else "workspaces/list.html"
        )
        return render(
            request,
            template,
            {
                "workplaces": [],
                "page_obj": None,
                "page_url_name": "workplace_list",
                "list_target": "#workplace-list",
            },
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
                return _workplace_form_success(request, "Workplace added.", page=1)
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


@login_required
def workplace_update(request, pk):
    workplace = get_object_or_404(Workplace, pk=pk, user=request.user)

    try:
        if request.method == "POST":
            form = WorkplaceForm(request.POST, instance=workplace)
            if form.is_valid():
                form.save()
                return _workplace_form_success(request, "Workplace updated.")
        else:
            form = WorkplaceForm(instance=workplace)

        return render(
            request,
            "workspaces/partials/modal_form.html",
            {"form": form, "workplace": workplace},
        )
    except Exception:
        form = WorkplaceForm(request.POST or None, instance=workplace)
        return render(
            request,
            "workspaces/partials/modal_form.html",
            {
                "form": form,
                "workplace": workplace,
                "error": "Could not update this workplace.",
            },
        )


@login_required
def workplace_delete(request, pk):
    workplace = get_object_or_404(Workplace, pk=pk, user=request.user)
    shift_count = workplace.shifts.count()
    can_delete = shift_count == 0

    try:
        if request.method == "POST":
            if not can_delete:
                return render(
                    request,
                    "workspaces/partials/modal_delete.html",
                    {
                        "workplace": workplace,
                        "shift_count": shift_count,
                        "can_delete": False,
                    },
                )

            workplace.delete()
            return _workplace_form_success(request, "Workplace deleted.")

        return render(
            request,
            "workspaces/partials/modal_delete.html",
            {
                "workplace": workplace,
                "shift_count": shift_count,
                "can_delete": can_delete,
            },
        )
    except ProtectedError:
        return render(
            request,
            "workspaces/partials/modal_delete.html",
            {
                "workplace": workplace,
                "shift_count": workplace.shifts.count(),
                "can_delete": False,
                "error": "This workplace still has shifts, so it cannot be deleted.",
            },
        )
    except Exception:
        return render(
            request,
            "workspaces/partials/modal_delete.html",
            {
                "workplace": workplace,
                "shift_count": shift_count,
                "can_delete": can_delete,
                "error": "Could not delete this workplace.",
            },
        )
