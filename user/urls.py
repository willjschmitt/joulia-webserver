"""URLS for the user app."""

from django.conf.urls import url

from user import views

urlpatterns = [
    url(r"api/user_preferences/$", views.UserPreferencesDetailView.as_view()),
    url(r"api/user_preferences/(?P<pk>[0-9]+)/$",
        views.UserPreferencesDetailView.as_view()),
]