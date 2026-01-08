import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from nav_spec import NavigationItem

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_user(db):
    user = User.objects.create_user(username="testuser", password="password")
    return user


@pytest.fixture
def user_with_perm(test_user):
    content_type = ContentType.objects.create(app_label="app", model="model")
    permission = Permission.objects.create(
        codename="can_view_special",
        name="Can View Special",
        content_type=content_type,
    )
    test_user.user_permissions.add(permission)
    return test_user


def test_basic_nav_spec_in_context(client, settings):
    settings.NAV_SPEC = [
        NavigationItem(title="Home", link="/", active_urls=["home"]),
        NavigationItem(title="Page A", link="/page-a/", active_urls=["page_a"]),
    ]
    response = client.get("/")
    assert "NAV_SPEC" in response.context
    nav_spec = response.context["NAV_SPEC"]
    assert len(nav_spec) == 2
    assert nav_spec[0].title == "Home"
    assert nav_spec[0].is_active
    assert not nav_spec[1].is_active


def test_nested_nav_active_state(client, settings):
    settings.NAV_SPEC = [
        NavigationItem(
            title="Parent",
            children=[
                NavigationItem(title="Page A", link="/page-a/", active_urls=["page_a"]),
            ],
        ),
    ]
    response = client.get("/page-a/")
    nav_spec = response.context["NAV_SPEC"]
    assert len(nav_spec) == 1
    parent = nav_spec[0]
    assert parent.is_active
    assert len(parent.children) == 1
    child = parent.children[0]
    assert child.is_active


def test_permission_based_display_user_lacks_perm(client, test_user, settings):
    settings.NAV_SPEC = [
        NavigationItem(title="Home", link="/"),
        NavigationItem(
            title="Special", link="/special/", displayed="app.can_view_special"
        ),
    ]
    client.login(username="testuser", password="password")
    response = client.get("/")
    nav_spec = response.context["NAV_SPEC"]
    assert len(nav_spec) == 1
    assert nav_spec[0].title == "Home"


def test_permission_based_display_user_has_perm(client, user_with_perm, settings):
    settings.NAV_SPEC = [
        NavigationItem(title="Home", link="/"),
        NavigationItem(
            title="Special", link="/special/", displayed="app.can_view_special"
        ),
    ]
    client.login(username="testuser", password="password")
    response = client.get("/")
    nav_spec = response.context["NAV_SPEC"]
    assert len(nav_spec) == 2
    assert nav_spec[1].title == "Special"


def test_callable_based_display(client, test_user, settings):
    settings.NAV_SPEC = [
        NavigationItem(title="Home", link="/"),
        NavigationItem(
            title="Staff Only", link="/staff/", displayed=lambda r: r.user.is_staff
        ),
    ]
    client.login(username="testuser", password="password")

    # As non-staff
    response = client.get("/")
    nav_spec = response.context["NAV_SPEC"]
    assert len(nav_spec) == 1

    # As staff
    test_user.is_staff = True
    test_user.save()
    response = client.get("/")
    nav_spec = response.context["NAV_SPEC"]
    assert len(nav_spec) == 2
    assert nav_spec[1].title == "Staff Only"


def test_dict_nav_spec_in_context(client, settings):
    settings.NAV_SPEC = {
        "main": [
            NavigationItem(title="Home", link="/", active_urls=["home"]),
        ],
        "footer": [
            NavigationItem(title="Page B", link="/page-b/", active_urls=["page_b"]),
        ],
    }
    response = client.get("/")
    assert "NAV_SPEC" in response.context
    nav_spec_dict = response.context["NAV_SPEC"]

    assert "main" in nav_spec_dict
    assert "footer" in nav_spec_dict

    main_nav = nav_spec_dict["main"]
    assert len(main_nav) == 1
    assert main_nav[0].title == "Home"
    assert main_nav[0].is_active

    footer_nav = nav_spec_dict["footer"]
    assert len(footer_nav) == 1
    assert not footer_nav[0].is_active


def test_empty_nav_spec(client, settings):
    settings.NAV_SPEC = []
    response = client.get("/")
    nav_spec = response.context["NAV_SPEC"]
    assert nav_spec == []


class TestCustomContextVariableName(TestCase):
    """Test custom context variable name configuration"""

    def test_custom_context_var_name_single_nav(self):
        """Test that NAV_SPEC_CONTEXT_VAR_NAME setting changes the context variable name"""
        with self.settings(
            NAV_SPEC_CONTEXT_VAR_NAME="site_navigation",
            NAV_SPEC=[
                NavigationItem(title="Home", link="/", active_urls=["home"]),
                NavigationItem(title="Page A", link="/page-a/", active_urls=["page_a"]),
            ],
        ):
            response = self.client.get("/")

            # Should NOT have NAV_SPEC in context
            self.assertNotIn("NAV_SPEC", response.context)

            # Should have custom name instead
            self.assertIn("site_navigation", response.context)
            nav_spec = response.context["site_navigation"]
            self.assertEqual(len(nav_spec), 2)
            self.assertEqual(nav_spec[0].title, "Home")
            self.assertTrue(nav_spec[0].is_active)

    def test_custom_context_var_name_multiple_navs(self):
        """Test that custom context var name works with dictionary navigation"""
        with self.settings(
            NAV_SPEC_CONTEXT_VAR_NAME="navigation",
            NAV_SPEC={
                "main": [
                    NavigationItem(title="Home", link="/", active_urls=["home"]),
                ],
                "footer": [
                    NavigationItem(
                        title="Page B", link="/page-b/", active_urls=["page_b"]
                    ),
                ],
            },
        ):
            response = self.client.get("/")

            # Should NOT have NAV_SPEC in context
            self.assertNotIn("NAV_SPEC", response.context)

            # Should have custom name instead
            self.assertIn("navigation", response.context)
            nav_dict = response.context["navigation"]

            self.assertIn("main", nav_dict)
            self.assertIn("footer", nav_dict)
            self.assertEqual(nav_dict["main"][0].title, "Home")
            self.assertEqual(nav_dict["footer"][0].title, "Page B")

    def test_default_context_var_name_when_not_configured(self):
        """Test backward compatibility - defaults to NAV_SPEC when not configured"""
        with self.settings(
            NAV_SPEC=[
                NavigationItem(title="Home", link="/"),
            ]
        ):
            response = self.client.get("/")

            # Should have default NAV_SPEC name
            self.assertIn("NAV_SPEC", response.context)
            self.assertEqual(len(response.context["NAV_SPEC"]), 1)
