from typing import Any

from django.conf import settings
from django.http import HttpRequest

from . import process_nav_spec


def nav_spec(request: HttpRequest) -> dict[str, Any]:
    # Get the context variable name from settings, default to 'NAV_SPEC'
    context_var_name = getattr(settings, "NAV_SPEC_CONTEXT_VAR_NAME", "NAV_SPEC")

    if isinstance(settings.NAV_SPEC, dict):
        context = {context_var_name: {}}
        for key, spec in settings.NAV_SPEC.items():
            context[context_var_name][key] = process_nav_spec(spec, request)
    else:
        context = {context_var_name: process_nav_spec(settings.NAV_SPEC, request)}
    return context
