'''
Created on Apr 14, 2016

@author: William
'''

from tornado.concurrent import Future
from tornado.httpclient import AsyncHTTPClient
from tornado.websocket import websocket_connect
from tornado import gen

import json
import requests
import logging
import datetime
import functools

from controls.settings import host

def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('__')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)

def rgetattr(obj, attr):
    return functools.reduce(getattr, [obj]+attr.split('__'))

@gen.coroutine #allows the websocket to be yielded
class subscribableVariable(object):
    '''
    classdocs
    '''
    dataIdentifyService = "http:" + host + "/live/timeseries/identify/"

    def __init__(self, instance, varName, sensorName,recipeInstance):
        '''
        Constructor
        '''
        self.instance = instance
        self.varName = varName
        
        #add new subscription to class vars
        self.subscribe(sensorName, recipeInstance, 'value')
        
    @property
    def value(self): return getattr(self.instance,self.varName)
    @value.setter
    def value(self,value): setattr(self.instance,self.varName,value)
        
    def subscribe(self,name,recipeInstance,type='value'):
        if ((name,recipeInstance)) not in self.subscribers:
            print('hi')
            r = requests.post(self.dataIdentifyService,data={'recipe_instance':recipeInstance,'name':name})
            idSensor = r.json()['sensor']
            self.subscribers[(idSensor,recipeInstance)] = (self,type)
            print('subscribing')
            self.websocket.write_message(json.dumps({'recipe_instance':recipeInstance,'sensor':idSensor,'subscribe':True}))
        
    @classmethod
    def on_message(cls,response):
        data = json.loads(response)
        print(data)
        subscriber = cls.subscribers((data['sensor'],data['recipeInstance']))
        subscriber[0].value = data['value']
    websocket = websocket_connect("ws:" + host + "/live/timeseries/socket/",on_message_callback=on_message)
    
    subscribers = {}

@gen.coroutine #allows the websocket to be yielded
class overridableVariable(object):
    '''
    classdocs
    '''
    dataIdentifyService = "http:" + host + "/live/timeseries/identify/"
    def __init__(self, sensorName,recipeInstance):
        '''
        Constructor
        '''
        self.value = None
        self.overridden = False
        
        #add new subscription to class vars
        self.subscribe(sensorName, recipeInstance, 'value')
        self.subscribe(sensorName+"Override", recipeInstance, 'override')
    
    def subscribe(self,name,recipeInstance,type='value'):
        if ((name,recipeInstance)) not in self.subscribers:
            r = requests.post(self.dataIdentifyService,data={'recipe_instance':recipeInstance,'name':name})
            idSensor = r.json()['sensor']
            self.subscribers[(idSensor,recipeInstance)] = (self,type)
            self.websocket.write_message(json.dumps({'recipe_instance':recipeInstance,'sensor':idSensor,'subscribe':True}))
        
    @classmethod
    def on_message(cls,response):
        data = json.loads(response)
        subscriber = cls.subscribers((data['sensor'],data['recipeInstance']))
        if subscriber[1] == 'value':
            subscriber[0].value = data['value']
        elif subscriber[1] == 'override':
            subscriber[0].overridden = data['value']
    websocket = websocket_connect("ws:" + host + "/live/timeseries/socket/",on_message_callback=on_message)
    
    subscribers = {}
    
class dataStreamer(object):
    timeOutWait = 10
    
    dataPostService = "http:" + host + "/live/timeseries/new/"
    dataIdentifyService = "http:" + host + "/live/timeseries/identify/"
    
    def __init__(self,streamingClass,recipeInstance):
        self.streamingClass = streamingClass
        self.recipeInstance = recipeInstance
        
        self.sensorMap = {}
        self.timeOutCounter = 0
        
    def register(self,attr,name=None):
        if name is None: name=attr #default to attribute as the name
        if name in self.sensorMap: raise AttributeError('{} already exists in streaming service.'.format(name)) #this makes sure we arent overwriting anything
        self.sensorMap[name] = {'attr':attr} #map the attribute to the server var name
    
    def postData(self):
        if self.timeOutCounter > 0:
            self.timeOutCounter -= 1
        else:
            #post temperature updates to server        
            sampleTime = str(datetime.datetime.now())
            
            for sensorName,sensor in self.sensorMap.iteritems():
                #get the sensor ID if we dont have it already
                if 'id' not in sensor:
                    try:
                        r = requests.post(self.dataIdentifyService,data={'recipe_instance':self.recipeInstance,'name':sensorName})
                        r.raise_for_status()
                    except requests.exceptions.ConnectionError:
                        logging.info("Server not there. Will retry later.")
                        self.timeOutCounter = self.timeOutWait
                        break
                    except requests.exceptions.HTTPError:
                        logging.info("Server returned error status. Will retry later.")
                        self.timeOutCounter = self.timeOutWait
                        break
                    
                    self.sensorMap['id'] = r.json()['sensor']
                    
                #send the data
                try:
                    r = requests.post(self.dataPostService,
                        data={'time':sampleTime,'recipe_instance':self.recipeInstance,
                            'value':rgetattr(self.streamingClass,sensor['attr']),'sensor':self.sensorMap['id']
                        }
                    )
                    r.raise_for_status()
                except requests.exceptions.ConnectionError:
                    logging.info("Server not there. Will retry later.")
                    self.timeOutCounter = self.timeOutWait
                    break
                except requests.exceptions.HTTPError:
                    logging.info("Server returned error status. Will retry later.")
                    self.timeOutCounter = self.timeOutWait
                    break
                    
        
    