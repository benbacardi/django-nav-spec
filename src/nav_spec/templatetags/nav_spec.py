from typing import Any

from django import template

from .. import NavigationItem, get_processed_nav_spec

register = template.Library()


@register.simple_tag(takes_context=True)
def get_nav_spec(
    context: dict[str, Any], key: str | None = None
) -> list[NavigationItem] | dict[str, list[NavigationItem]]:
    """
    Get the processed navigation spec.

    Usage:
        {% load nav_spec %}
        {% get_nav_spec as nav %}
        {% get_nav_spec "header" as header_nav %}
    """
    return get_processed_nav_spec(context["request"], key)
