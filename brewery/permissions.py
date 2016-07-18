'''
Created on Jul 17, 2016

@author: Will
'''
from rest_framework import permissions

class IsMemberOfBrewingCompany(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_member_of_brewing_company(request.user,obj)
    
def is_member_of_brewing_company(user,brewery):
    return user in brewery.company.group.user_set.all()