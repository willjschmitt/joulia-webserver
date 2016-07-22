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
        
        brewerys = Brewery.objects.filter(company__group__in=self.request.user.groups.all())
        
        locations = list(map(lambda x:x.location, brewerys))
        context['locations']  = []
        for location in locations:
            location_brewerys = [brewery for brewery in brewerys if brewery.location==location]
            context['locations'].append({'location':location,'brewerys':location_brewerys})
        return context