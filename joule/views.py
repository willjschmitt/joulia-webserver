'''
Created on Jun 21, 2016

@author: Will
'''

from django.views.generic.base import TemplateView

from brewery.models import Brewery

class IndexView(TemplateView):
    template_name = "index.html"
    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        
        context['brewerys'] = Brewery.objects.all()
        
        return context