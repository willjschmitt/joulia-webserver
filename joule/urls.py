"""joule URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from django.conf.urls import url,include

from django.contrib.auth.decorators import login_required

from .views import IndexView

from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin

import social_django.views as social_views

urlpatterns = [
    url(r'^$', login_required(IndexView.as_view())),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
    url('^', include('brewery.urls')),

    url('', include('social_django.urls', namespace='social')),
    url(r'^login/google-oauth2/$', social_views.auth,
        name='login-google-oauth2')
]  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)