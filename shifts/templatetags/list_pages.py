from django import template

from config.pagination import list_page_url

register = template.Library()


@register.simple_tag
def list_href(url_name, page, query=None):
    return list_page_url(url_name, page, query or None)
