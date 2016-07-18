'''
Created on Jul 18, 2016

@author: Will
'''
from django.conf import settings
import django.contrib.auth
from importlib import import_module

def get_current_user(info):
    engine = import_module(settings.SESSION_ENGINE)
    session_key = str(info.get_cookie(settings.SESSION_COOKIE_NAME))

    class Dummy(object):
        pass

    django_request = Dummy()
    django_request.session = engine.SessionStore(session_key)
    user = django.contrib.auth.get_user(django_request)
    return user