"""URLS for the auth app."""

from django.conf.urls import url

from auth import views

urlpatterns = [
    url(r"api/user/$", views.UserView.as_view()),
]