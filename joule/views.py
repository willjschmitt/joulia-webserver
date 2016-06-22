'''
Created on Jun 21, 2016

@author: Will
'''

from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

@login_required
class IndexView(TemplateView):
    template_name = "index.html"