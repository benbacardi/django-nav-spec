import importlib.metadata
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.http import HttpRequest

try:
    __version__ = importlib.metadata.version("django-nav-spec")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"


class NavigationItem:
    def __init__(
        self,
        title: str,
        link: str | None = None,
        children: list["NavigationItem"] | None = None,
        active_urls: list[str] | None = None,
        displayed: str | Callable[[HttpRequest], bool] | None = None,
        is_active: Callable[[HttpRequest], bool] | None = None,
        request: HttpRequest | None = None,
        **kwargs: Any,
    ) -> None:
        self.title = title
        self.link = link
        self.children = children or []
        self.active_urls = active_urls or []
        self.request = request
        self.active_func = is_active
        self.displayed = displayed
        self.kwargs = kwargs

    @property
    def is_active(self) -> bool:
        if not self.request:
            return False
        if self.children:
            return any(c.is_active for c in self.children)
        if (
            self.active_urls
            and self.request.resolver_match
            and self.request.resolver_match.url_name in self.active_urls
        ):
            return True
        if self.active_func and self.active_func(self.request):
            return True
        return False

    def is_displayed(self, request: HttpRequest) -> bool:
        if self.children and not self.displayed:
            return any(c.is_displayed(request) for c in self.children)
        if self.displayed:
            if isinstance(self.displayed, str) and not request.user.has_perm(
                self.displayed
            ):
                return False
            if callable(self.displayed) and not self.displayed(request):
                return False
        return True

    def copy_for_display(self, request: HttpRequest) -> "NavigationItem | None":
        if not self.is_displayed(request):
            return None
        displayed_children: list[NavigationItem] | None = None
        if self.children:
            displayed_children = [
                copied
                for c in self.children
                if c.is_displayed(request)
                and (copied := c.copy_for_display(request)) is not None
            ]
        return NavigationItem(
            title=self.title,
            link=self.link,
            children=displayed_children,
            active_urls=self.active_urls,
            displayed=self.displayed,
            is_active=self.active_func,
            request=request,
            **self.kwargs,
        )


def process_nav_spec(
    spec: list[NavigationItem], request: HttpRequest
) -> list[NavigationItem]:
    filtered_nav = [nav.copy_for_display(request) for nav in spec]
    return [nav for nav in filtered_nav if nav]


def get_processed_nav_spec(
    request: HttpRequest, key: str | None = None
) -> list[NavigationItem] | dict[str, list[NavigationItem]]:
    """
    Get processed navigation spec from settings.

    If NAV_SPEC is a dict and key is provided, returns the processed spec for that key.
    If NAV_SPEC is a dict and no key is provided, returns dict of all processed specs.
    If NAV_SPEC is a list, returns the processed list.
    """
    if isinstance(settings.NAV_SPEC, dict):
        if key:
            spec = settings.NAV_SPEC.get(key, [])
            return process_nav_spec(spec, request)
        else:
            return {
                k: process_nav_spec(v, request)
                for k, v in settings.NAV_SPEC.items()
            }
    else:
        return process_nav_spec(settings.NAV_SPEC, request)
