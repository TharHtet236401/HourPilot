from urllib.parse import parse_qs, urlparse

from django.core.paginator import Paginator
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


def list_page_url(url_name, page_number):
    url = reverse(url_name)
    if int(page_number) > 1:
        return f"{url}?page={page_number}"
    return url
