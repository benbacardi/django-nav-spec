from unittest.mock import MagicMock

import pytest
from django.template import Context, Template

from nav_spec import NavigationItem, get_processed_nav_spec, process_nav_spec


@pytest.fixture
def mock_request():
    request = MagicMock()
    request.user = MagicMock()
    request.resolver_match = MagicMock()
    return request


class TestNavigationItemIsActive:
    def test_is_active_no_conditions(self, mock_request):
        item = NavigationItem(title="Test", request=mock_request)
        assert not item.is_active

    def test_is_active_matching_url_name(self, mock_request):
        mock_request.resolver_match.url_name = "page_a"
        item = NavigationItem(
            title="Test", active_urls=["page_a"], request=mock_request
        )
        assert item.is_active

    def test_is_active_no_matching_url_name(self, mock_request):
        mock_request.resolver_match.url_name = "page_b"
        item = NavigationItem(
            title="Test", active_urls=["page_a"], request=mock_request
        )
        assert not item.is_active

    def test_is_active_callable_true(self, mock_request):
        item = NavigationItem(
            title="Test", is_active=lambda r: True, request=mock_request
        )
        assert item.is_active

    def test_is_active_callable_false(self, mock_request):
        item = NavigationItem(
            title="Test", is_active=lambda r: False, request=mock_request
        )
        assert not item.is_active

    def test_parent_is_active_if_child_is_active(self, mock_request):
        mock_request.resolver_match.url_name = "child_page"
        child = NavigationItem(
            title="Child", active_urls=["child_page"], request=mock_request
        )
        parent = NavigationItem(title="Parent", children=[child], request=mock_request)
        assert child.is_active
        assert parent.is_active

    def test_parent_is_not_active_if_no_child_is_active(self, mock_request):
        child = NavigationItem(title="Child", request=mock_request)
        parent = NavigationItem(title="Parent", children=[child], request=mock_request)
        assert not child.is_active
        assert not parent.is_active


class TestNavigationItemIsDisplayed:
    def test_is_displayed_by_default(self, mock_request):
        item = NavigationItem(title="Test")
        assert item.is_displayed(mock_request)

    def test_is_displayed_permission_success(self, mock_request):
        mock_request.user.has_perm.return_value = True
        item = NavigationItem(title="Test", displayed="some.permission")
        assert item.is_displayed(mock_request)
        mock_request.user.has_perm.assert_called_with("some.permission")

    def test_is_displayed_permission_fail(self, mock_request):
        mock_request.user.has_perm.return_value = False
        item = NavigationItem(title="Test", displayed="some.permission")
        assert not item.is_displayed(mock_request)

    def test_is_displayed_callable_true(self, mock_request):
        item = NavigationItem(title="Test", displayed=lambda r: True)
        assert item.is_displayed(mock_request)

    def test_is_displayed_callable_false(self, mock_request):
        item = NavigationItem(title="Test", displayed=lambda r: False)
        assert not item.is_displayed(mock_request)

    def test_parent_is_displayed_if_child_is(self, mock_request):
        child = NavigationItem(title="Child", displayed=lambda r: True)
        parent = NavigationItem(title="Parent", children=[child])
        assert parent.is_displayed(mock_request)

    def test_parent_is_not_displayed_if_child_is_not(self, mock_request):
        child = NavigationItem(title="Child", displayed=lambda r: False)
        parent = NavigationItem(title="Parent", children=[child])
        assert not parent.is_displayed(mock_request)


class TestProcessNavSpec:
    def test_process_nav_spec_filters_items(self, mock_request):
        spec = [
            NavigationItem(title="Visible", displayed=lambda r: True),
            NavigationItem(title="Hidden", displayed=lambda r: False),
        ]
        processed = process_nav_spec(spec, mock_request)
        assert len(processed) == 1
        assert processed[0].title == "Visible"

    def test_process_nav_spec_empty_list(self, mock_request):
        spec = []
        processed = process_nav_spec(spec, mock_request)
        assert processed == []

    def test_process_nav_spec_nested_filtering(self, mock_request):
        child_visible = NavigationItem(title="Child Visible", displayed=lambda r: True)
        child_hidden = NavigationItem(title="Child Hidden", displayed=lambda r: False)

        parent1 = NavigationItem(
            title="Parent 1", children=[child_visible, child_hidden]
        )
        parent2 = NavigationItem(title="Parent 2", children=[child_hidden])
        parent3 = NavigationItem(
            title="Parent 3", displayed=lambda r: False, children=[child_visible]
        )

        spec = [parent1, parent2, parent3]
        processed = process_nav_spec(spec, mock_request)

        # parent1 should be visible, but only with the visible child
        # parent2 should not be visible as its only child is hidden
        # parent3 should not be visible as it's explicitly hidden
        assert len(processed) == 1
        assert processed[0].title == "Parent 1"
        assert len(processed[0].children) == 1
        assert processed[0].children[0].title == "Child Visible"


class TestNavigationItemCopyForDisplay:
    def test_copy_for_display_not_displayed(self, mock_request):
        item = NavigationItem(title="Test", displayed=lambda r: False)
        assert item.copy_for_display(mock_request) is None

    def test_copy_for_display_simple(self, mock_request):
        item = NavigationItem(title="Test", link="/test", displayed=lambda r: True)
        new_item = item.copy_for_display(mock_request)
        assert new_item is not None
        assert new_item.title == "Test"
        assert new_item.link == "/test"
        assert new_item.request == mock_request

    def test_copy_for_display_with_children(self, mock_request):
        child_visible = NavigationItem(title="Child Visible", displayed=lambda r: True)
        child_hidden = NavigationItem(title="Child Hidden", displayed=lambda r: False)
        parent = NavigationItem(title="Parent", children=[child_visible, child_hidden])

        new_parent = parent.copy_for_display(mock_request)

        assert new_parent is not None
        assert len(new_parent.children) == 1
        assert new_parent.children[0].title == "Child Visible"


class TestGetProcessedNavSpec:
    def test_simple_list_nav_spec(self, mock_request, settings):
        settings.NAV_SPEC = [
            NavigationItem(title="Home", link="/"),
            NavigationItem(title="About", link="/about/"),
        ]
        result = get_processed_nav_spec(mock_request)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].title == "Home"
        assert result[1].title == "About"

    def test_dict_nav_spec_without_key(self, mock_request, settings):
        settings.NAV_SPEC = {
            "header": [NavigationItem(title="Home", link="/")],
            "footer": [NavigationItem(title="Privacy", link="/privacy/")],
        }
        result = get_processed_nav_spec(mock_request)
        assert isinstance(result, dict)
        assert "header" in result
        assert "footer" in result
        assert len(result["header"]) == 1
        assert result["header"][0].title == "Home"
        assert len(result["footer"]) == 1
        assert result["footer"][0].title == "Privacy"

    def test_dict_nav_spec_with_key(self, mock_request, settings):
        settings.NAV_SPEC = {
            "header": [NavigationItem(title="Home", link="/")],
            "footer": [NavigationItem(title="Privacy", link="/privacy/")],
        }
        result = get_processed_nav_spec(mock_request, key="header")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].title == "Home"

    def test_dict_nav_spec_with_missing_key(self, mock_request, settings):
        settings.NAV_SPEC = {
            "header": [NavigationItem(title="Home", link="/")],
        }
        result = get_processed_nav_spec(mock_request, key="nonexistent")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_filters_by_permission(self, mock_request, settings):
        mock_request.user.has_perm.return_value = False
        settings.NAV_SPEC = [
            NavigationItem(title="Public", link="/"),
            NavigationItem(title="Admin", link="/admin/", displayed="app.view_admin"),
        ]
        result = get_processed_nav_spec(mock_request)
        assert len(result) == 1
        assert result[0].title == "Public"

    def test_filters_by_callable(self, mock_request, settings):
        mock_request.user.is_staff = False
        settings.NAV_SPEC = [
            NavigationItem(title="Public", link="/"),
            NavigationItem(
                title="Staff", link="/staff/", displayed=lambda r: r.user.is_staff
            ),
        ]
        result = get_processed_nav_spec(mock_request)
        assert len(result) == 1
        assert result[0].title == "Public"

    def test_preserves_active_state(self, mock_request, settings):
        mock_request.resolver_match.url_name = "home"
        settings.NAV_SPEC = [
            NavigationItem(title="Home", link="/", active_urls=["home"]),
            NavigationItem(title="About", link="/about/", active_urls=["about"]),
        ]
        result = get_processed_nav_spec(mock_request)
        assert result[0].is_active
        assert not result[1].is_active

    def test_empty_list(self, mock_request, settings):
        settings.NAV_SPEC = []
        result = get_processed_nav_spec(mock_request)
        assert result == []

    def test_empty_dict(self, mock_request, settings):
        settings.NAV_SPEC = {}
        result = get_processed_nav_spec(mock_request)
        assert result == {}


class TestGetNavSpecTemplateTag:
    def test_simple_list_nav_spec(self, mock_request, settings):
        settings.NAV_SPEC = [
            NavigationItem(title="Home", link="/"),
            NavigationItem(title="About", link="/about/"),
        ]
        template = Template(
            "{% load nav_spec %}{% get_nav_spec as nav %}"
            "{% for item in nav %}{{ item.title }},{% endfor %}"
        )
        context = Context({"request": mock_request})
        output = template.render(context)
        assert "Home," in output
        assert "About," in output

    def test_dict_nav_spec_without_key(self, mock_request, settings):
        settings.NAV_SPEC = {
            "header": [NavigationItem(title="Home", link="/")],
            "footer": [NavigationItem(title="Privacy", link="/privacy/")],
        }
        template = Template(
            "{% load nav_spec %}{% get_nav_spec as nav %}"
            "{{ nav.header.0.title }},{{ nav.footer.0.title }}"
        )
        context = Context({"request": mock_request})
        output = template.render(context)
        assert "Home," in output
        assert "Privacy" in output

    def test_dict_nav_spec_with_key(self, mock_request, settings):
        settings.NAV_SPEC = {
            "header": [NavigationItem(title="Home", link="/")],
            "footer": [NavigationItem(title="Privacy", link="/privacy/")],
        }
        template = Template(
            "{% load nav_spec %}{% get_nav_spec 'header' as header_nav %}"
            "{% for item in header_nav %}{{ item.title }}{% endfor %}"
        )
        context = Context({"request": mock_request})
        output = template.render(context)
        assert "Home" in output
        assert "Privacy" not in output

    def test_dict_nav_spec_with_missing_key(self, mock_request, settings):
        settings.NAV_SPEC = {
            "header": [NavigationItem(title="Home", link="/")],
        }
        template = Template(
            "{% load nav_spec %}{% get_nav_spec 'nonexistent' as nav %}"
            "{% if nav %}HAS_NAV{% else %}NO_NAV{% endif %}"
        )
        context = Context({"request": mock_request})
        output = template.render(context)
        assert "NO_NAV" in output

    def test_active_state_in_template(self, mock_request, settings):
        mock_request.resolver_match.url_name = "home"
        settings.NAV_SPEC = [
            NavigationItem(title="Home", link="/", active_urls=["home"]),
            NavigationItem(title="About", link="/about/", active_urls=["about"]),
        ]
        template = Template(
            "{% load nav_spec %}{% get_nav_spec as nav %}"
            "{% for item in nav %}"
            "{% if item.is_active %}ACTIVE:{{ item.title }}{% endif %}"
            "{% endfor %}"
        )
        context = Context({"request": mock_request})
        output = template.render(context)
        assert "ACTIVE:Home" in output
        assert "ACTIVE:About" not in output

    def test_permission_filtering(self, mock_request, settings):
        mock_request.user.has_perm.return_value = False
        settings.NAV_SPEC = [
            NavigationItem(title="Public", link="/"),
            NavigationItem(title="Admin", link="/admin/", displayed="app.view_admin"),
        ]
        template = Template(
            "{% load nav_spec %}{% get_nav_spec as nav %}"
            "{% for item in nav %}{{ item.title }},{% endfor %}"
        )
        context = Context({"request": mock_request})
        output = template.render(context)
        assert "Public," in output
        assert "Admin" not in output

    def test_callable_filtering(self, mock_request, settings):
        mock_request.user.is_staff = False
        settings.NAV_SPEC = [
            NavigationItem(title="Public", link="/"),
            NavigationItem(
                title="Staff", link="/staff/", displayed=lambda r: r.user.is_staff
            ),
        ]
        template = Template(
            "{% load nav_spec %}{% get_nav_spec as nav %}"
            "{% for item in nav %}{{ item.title }},{% endfor %}"
        )
        context = Context({"request": mock_request})
        output = template.render(context)
        assert "Public," in output
        assert "Staff" not in output

    def test_nested_navigation(self, mock_request, settings):
        settings.NAV_SPEC = [
            NavigationItem(
                title="Parent",
                children=[
                    NavigationItem(title="Child 1", link="/child1/"),
                    NavigationItem(title="Child 2", link="/child2/"),
                ],
            ),
        ]
        template = Template(
            "{% load nav_spec %}{% get_nav_spec as nav %}"
            "{{ nav.0.title }}:"
            "{% for child in nav.0.children %}{{ child.title }},{% endfor %}"
        )
        context = Context({"request": mock_request})
        output = template.render(context)
        assert "Parent:" in output
        assert "Child 1," in output
        assert "Child 2," in output

    def test_empty_nav_spec(self, mock_request, settings):
        settings.NAV_SPEC = []
        template = Template(
            "{% load nav_spec %}{% get_nav_spec as nav %}"
            "{% if nav %}HAS_NAV{% else %}NO_NAV{% endif %}"
        )
        context = Context({"request": mock_request})
        output = template.render(context)
        assert "NO_NAV" in output
