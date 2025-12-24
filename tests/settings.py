
from __future__ import annotations

SECRET_KEY = "dummy"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "nav_spec.context_processors.nav_spec",
            ],
        },
    }
]

ROOT_URLCONF = "tests.urls"

# This is where the library will look for the navigation spec
NAV_SPEC = []
