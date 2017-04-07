"""Root urls for the joulia-webserver project.
"""

from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView

import social_django.views as social_views

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name="index.html")),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
    url('^', include('brewery.urls')),

    url('', include('social_django.urls', namespace='social')),
    url(r'^login/google-oauth2/$', social_views.auth,
        name='login-google-oauth2')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
