from typing import Any

from django.conf import settings
from django.http import HttpRequest

from . import get_processed_nav_spec


def nav_spec(request: HttpRequest) -> dict[str, Any]:
    context_var_name = getattr(settings, "NAV_SPEC_CONTEXT_VAR_NAME", "NAV_SPEC")
    return {context_var_name: get_processed_nav_spec(request)}
