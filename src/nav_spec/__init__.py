import importlib.metadata


try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"


class NavigationItem:
    def __init__(
        self,
        title,
        link=None,
        children=None,
        active_urls=None,
        displayed=None,
        is_active=None,
        request=None,
        **kwargs,
    ):
        self.title = title
        self.link = link
        self.children = children or []
        self.active_urls = active_urls or []
        self.request = request
        self.active_func = is_active
        self.displayed = displayed
        self.kwargs = kwargs

    @property
    def is_active(self):
        if not self.request:
            return False
        if self.children:
            return any(c.is_active for c in self.children)
        if (
            self.active_urls
            and self.request.resolver_match.url_name in self.active_urls
        ):
            return True
        if self.active_func and self.active_func(self.request):
            return True
        return False

    def is_displayed(self, request):
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

    def copy_for_display(self, request):
        if not self.is_displayed(request):
            return None
        if self.children:
            displayed_children = [
                c.copy_for_display(request)
                for c in self.children
                if c.is_displayed(request)
            ]
        else:
            displayed_children = None
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


def process_nav_spec(spec, request):
    filtered_nav = [nav.copy_for_display(request) for nav in spec]
    return [nav for nav in filtered_nav if nav]
