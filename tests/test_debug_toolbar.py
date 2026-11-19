from django.conf import settings
from django.test import Client
from django.urls import resolve, reverse


def test_debug_toolbar_is_configured_for_local_development() -> None:
    assert "debug_toolbar" in settings.INSTALLED_APPS
    assert (
        "debug_toolbar.middleware.DebugToolbarMiddleware"
        in settings.MIDDLEWARE
    )
    assert "127.0.0.1" in settings.INTERNAL_IPS


def test_debug_toolbar_routes_are_available_in_debug_mode() -> None:
    assert settings.DEBUG is True

    toolbar_url = reverse("djdt:render_panel")

    assert toolbar_url == "/__debug__/render_panel/"
    assert resolve(toolbar_url).namespace == "djdt"


def test_debug_toolbar_rejects_non_internal_address() -> None:
    response = Client(
        HTTP_HOST="localhost",
        REMOTE_ADDR="203.0.113.10",
    ).get(reverse("djdt:render_panel"))

    assert response.status_code == 404
