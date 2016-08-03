'''
Created on Jul 17, 2016

@author: Will
'''
from rest_framework import permissions

class IsMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_member_of_brewing_company(request.user,obj)
    
class IsMemberOfBrewingCompany(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_member_of_brewing_company(request.user,obj.company)

class IsMemberOfBrewery(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_member_of_brewing_company(request.user,obj.brewery.company)

    
def is_member_of_brewing_company(user,brewing_company):
    try:
        return user in brewing_company.group.user_set.all()
    except:
        False #incase we dont have a company assigned right