"""Root urls for the joulia-webserver project.
"""

from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
import social_django.views as social_views

import brewery.views as brewery_views

urlpatterns = [
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^brewery/', include('brewery.urls')),
    url(r'^auth/', include('auth.urls')),

    url(r"live/timeseries/new/$", brewery_views.TimeSeriesNewHandler.as_view()),
    url(r"live/timeseries/identify/$",
        brewery_views.TimeSeriesIdentifyHandler.as_view()),

    url('', include('social_django.urls', namespace='social')),
    url(r'^login/google-oauth2/$', social_views.auth,
        name='login-google-oauth2')
]
