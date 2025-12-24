
from django.urls import path

from . import views

urlpatterns = [
    path("", views.test_view, name="home"),
    path("page-a/", views.test_view, name="page_a"),
    path("page-b/", views.test_view, name="page_b"),
]
