from django.conf import settings

from . import process_nav_spec


def nav_spec(request):
    if isinstance(settings.NAV_SPEC, dict):
        context = {
            "NAV_SPEC": {}
        }
        for key, spec in settings.NAV_SPEC.items():
            context["NAV_SPEC"][key] = process_nav_spec(spec, request)
    else:
        context = {
            "NAV_SPEC": process_nav_spec(settings.NAV_SPEC, request)
        }
    return context
