from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse,HttpResponseNotAllowed,HttpResponseBadRequest,HttpResponseForbidden

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from . import permissions

from . import models
from . import serializers

import logging
import json
import subprocess
from jinja2 import Template

'''
brewery type views
'''
class BrewingCompanyApiView():
    queryset = models.BrewingCompany.objects.all()
    serializer_class = serializers.BrewingCompanySerializer
    permission_classes = (IsAuthenticated,permissions.IsMember)
class BrewingCompanyListView(BrewingCompanyApiView,generics.ListCreateAPIView): pass
class BrewingCompanyDetailView(BrewingCompanyApiView,generics.RetrieveUpdateDestroyAPIView): pass

class BreweryApiView():
    queryset = models.Brewery.objects.all()
    serializer_class = serializers.BrewerySerializer
    permission_classes = (IsAuthenticated,permissions.IsMemberOfBrewingCompany)
class BreweryListView(BreweryApiView,generics.ListCreateAPIView): pass
class BreweryDetailView(BreweryApiView,generics.RetrieveUpdateDestroyAPIView): pass
    
class BrewhouseApiView():
    queryset = models.Brewhouse.objects.all()
    serializer_class = serializers.BrewhouseSerializer
    permission_classes = (IsAuthenticated,permissions.IsMemberOfBrewery)
    filter_fields = ('id', 'brewery', )
class BrewhouseListView(BrewhouseApiView,generics.ListCreateAPIView):
    def perform_create(self, serializer):
        '''Overridden mixin function in order to call creation of 
        simulated brewhouse if appropriate'''
        
        instance = serializer.save()
        
        if instance.simulated:
            instance_id = add_simulated_brewhouse(serializer)
            instance.ec2_instance_id = instance_id
            instance.save()
            
    
class BrewhouseDetailView(BrewhouseApiView,generics.RetrieveUpdateDestroyAPIView): pass


'''
Recipe type views
'''
class BeerStyleListView(generics.ListCreateAPIView):
    queryset = models.BeerStyle.objects.all()
    serializer_class = serializers.BeerStyleSerializer

class RecipeListView(generics.ListCreateAPIView):
    queryset = models.Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer

class RecipeInstanceListView(generics.ListCreateAPIView):
    queryset = models.RecipeInstance.objects.all()
    serializer_class = serializers.RecipeInstanceSerializer
    filter_fields = ('id', 'active','brewhouse',)

class TimeSeriesNewHandler(generics.CreateAPIView):
    queryset = models.TimeSeriesDataPoint.objects.all()
    serializer_class = serializers.TimeSeriesDataPointSerializer


def add_simulated_brewhouse(brewhouse):
    '''Requests AWS to initialize new ec2 instance using the shell script
    to install Docker then start a container with the Brewhouse in it
    
    Args:
        brewhouse: The `Brewhouse` object to use for binding to the new
            AWS EC2 instance.
            
    Returns: Instance id for the 
    '''
    authtoken=brewhouse.token.key
    startup_template = Template('"'
                                +'#!/bin/bash\n'
                                +'sudo yum update -y\n'
                                +'sudo yum install -y docker\n'
                                +'sudo service docker start\n'
                                +'sudo usermod -a -G docker ec2-user\n'
                                +'echo export joulia-webserver-host=joulia.io >> /etc/environment\n'
                                +'echo export joulia-webserver-authtoken={} >> /etc/environment\n'.format(authtoken)
                                +'docker run willjschmitt/joulia-controller\n'
                                +'"')
    startup_script = startup_template.render()
    
    # Build our aws cli command to instantiate the new instance
    aws_args = ['ec2','run-instances']
    ec2_kwargs = {'instance-type':'t2.nano',
                  'image-id':'ami-6869aa05',
                  'region':'us-east-1',
                  'key-name':"schmitwi default",
                  'security-groups': 'joulia-brewhouse-controllers',
                  'user-data':startup_script}
    
    
    cmd = ['aws']
    cmd += aws_args
    for name,value in ec2_kwargs.iteritems():
        cmd.append("--{}={}".format(name,value))
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    result_data = json.loads(proc.communicate()[0])
    
    instance_id = result_data['Instances'][0]['InstanceId']
    
    return instance_id
    

class TimeSeriesIdentifyHandler(APIView):
    '''Identifies a time series group by the name of an AssetSensor.
    
    Can only be handled as a POST request.
    '''
    def post(self,request,*args,**kwargs):
        '''Identifies a time series group by the name of an AssetSensor.
        
        If the AssetSensor does not yet exist, creates it.
        
        Args:
            recipe_instance: (Optional) POST argument with the 
                recipe_instance pk. Used to retrieve the Brewhouse
                equipment associated with the request. Used for some 
                cases when the equipment has more readily available 
                access to the recipe_instance rather than the Brewhouse
                directly.
            brewhouse: (Optional): POST argument with the Brewhouse
                pk. Required if recipe_instance is not submitted.
            name: Name for the AssetSensor to be used in the time
                series data. See AssetSensor for more information on
                naming.
                
        Returns: JsonResponse with the pk to the sensor as the property
            "sensor". Response status is 200 if just returning object
            and 201 if needed to create a new AssetSensor.
        '''
        try:#see if we can get an existing AssetSensor
            if 'recipe_instance' in request.data:
                recipe_instance_id = request.data['recipe_instance']
                recipe_instance = models.RecipeInstance.objects.get(id=recipe_instance_id)
                brewhouse = recipe_instance.brewhouse
            else:
                brewhouse_id = request.data['brewhouse']
                brewhouse = models.Brewhouse.objects.get(id=brewhouse_id)
            
            name = request.data['name']
            sensor = models.AssetSensor.objects.get(name=name,
                                                    brewery=brewhouse)
            status_code = status.HTTP_200_OK
        except ObjectDoesNotExist: #otherwise create one for recording data
            logging.debug('Creating new asset sensor {} for asset {}'
                          ''.format(request.data['name'],brewhouse))
            sensor = models.AssetSensor(name=name,
                                        brewery=brewhouse)
            sensor.save()
            status_code = status.HTTP_201_CREATED
        response = JsonResponse({'sensor':sensor.pk})
        response.status_code=status_code
        return response

'''
operational views
'''
@login_required  
def launch_recipe_instance(request):
    '''Starts a RecipeInstance on a given Brewhouse.
    
    Must be submitted as a POST request.
    
    Args:
        recipe: POST argument for the recipe to run on the Brewhouse
        brewhouse: POST argument for the Brewhouse to launch the
            recipe on
            
    Raises:
        HttpResponseNotAllowed: if the request is not submitted as POST
        HttpResponseForbidden: if the user is not associated with
            the BrewingCompany that owns the Brewhouse requested
        HttpResponseBadRequest: if the brewery is already active
    Returns: JsonResponse if the brewhouse is successfully activated.
            Contains the pk to the newly instantiated instance as
            property "recipe_instance".
    '''  
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    data = json.loads(request.body)
    recipe = models.Recipe.objects.get(pk=data['recipe'])
    brewhouse = models.Brewhouse.objects.get(pk=data['brewhouse'])
    brewery = brewhouse.brewery
    
    if not permissions.is_member_of_brewing_company(request.user,brewery.company):
        return HttpResponseForbidden('Access not permitted to brewing equipment.')
    
    if models.RecipeInstance.objects.filter(brewhouse=brewhouse,
                                            active=True).count()!=0:
        return HttpResponseBadRequest('Brewery is already active')

    else:
        new_instance = models.RecipeInstance(recipe=recipe,
                                             brewhouse=brewhouse,
                                             active=True)
        new_instance.save()
        return JsonResponse({'recipe_instance':new_instance.pk})
    
@login_required  
def end_recipe_instance(request):
    '''Stops an already running RecipeInstance.
    
    Must be submitted as a POST request.
    
    Args:
        recipe_instance: POST argument for the recipe_instance
            currently running on equipment
            
    Raises:
        HttpResponseNotAllowed: if the request is not submitted as POST
        HttpResponseForbidden: if the user is not associated with
            the BrewingCompany that owns the Brewhouse associated
            with the recipe_instance
        HttpResponseBadRequest: if the recipe_instance is not active
    Returns: JsonResponse if the brewhouse is successfully deactivated.
            Response is an empty Json object.
    '''  
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data = json.loads(request.body)
    recipe_instance = models.RecipeInstance.objects.get(pk=data['recipe_instance'])
    brewhouse = recipe_instance.brewhouse
    brewery = brewhouse.brewery
    
    if not permissions.is_member_of_brewing_company(request.user,brewery.company):
        return HttpResponseForbidden('Access not permitted to brewing equipment.')
    
    if not recipe_instance.active:
        return HttpResponseBadRequest('Recipe instance requested was'
                                      ' not an active instance.')
    recipe_instance.active = False
    recipe_instance.save()
    
    return JsonResponse({})