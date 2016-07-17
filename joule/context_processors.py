'''
Created on Jul 17, 2016

@author: Will
'''
from django.conf import settings # import the settings file

def site_name(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'SITE_NAME': settings.SITE_NAME}