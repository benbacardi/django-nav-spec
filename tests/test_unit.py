from unittest.mock import MagicMock, patch

import pytest

from nav_spec import NavigationItem, process_nav_spec
from nav_spec.context_processors import nav_spec as nav_spec_context_processor


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
