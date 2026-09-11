from urllib.parse import parse_qs, urlparse

from django.core.paginator import Paginator
from django.http import QueryDict
from django.urls import reverse

SHIFT_PAGE_SIZE = 10
WORKPLACE_PAGE_SIZE = 8


def page_number_from_request(request, default=1):
    page = request.GET.get("page")
    if page:
        return page

    current = request.headers.get("HX-Current-URL", "")
    if current:
        values = parse_qs(urlparse(current).query).get("page")
        if values:
            return values[0]
    return default


def paginate(queryset, page, per_page):
    return Paginator(queryset, per_page).get_page(page)


def query_without_page(query=None):
    params = QueryDict(mutable=True)
    if not query:
        return params

    if hasattr(query, "lists"):
        params = query.copy()
        params._mutable = True
    else:
        params.update(query)

    params.pop("page", None)
    for key in list(params.keys()):
        values = [value for value in params.getlist(key) if value != ""]
        if values:
            params.setlist(key, values)
        else:
            del params[key]
    return params


def list_page_url(url_name, page_number, query=None):
    url = reverse(url_name)
    params = query_without_page(query)
    if int(page_number) > 1:
        params["page"] = str(int(page_number))
    encoded = params.urlencode()
    return f"{url}?{encoded}" if encoded else url
