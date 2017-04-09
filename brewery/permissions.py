"""Django rest framework permissions for the brewery app rest end points.
"""

from rest_framework import permissions


class IsMember(permissions.BasePermission):
    """Checks the current user is a member of the requested brewing company."""
    def has_object_permission(self, request, view, brewing_company):
        return is_member_of_brewing_company(request.user, brewing_company)


class IsMemberOfBrewingCompany(permissions.BasePermission):
    """Checks the current user is a member of the brewing company associated
    with the requested brewery.
    """
    def has_object_permission(self, request, view, brewery):
        return is_member_of_brewing_company(request.user, brewery.company)


class IsMemberOfBrewery(permissions.BasePermission):
    """Checks the current user is a member of the brewing company that owns the
    brewery the brewing equipment is associated with.
    """
    def has_object_permission(self, request, view, brewing_equipment):
        brewing_company = brewing_equipment.brewery.company
        return is_member_of_brewing_company(request.user, brewing_company)

    
def is_member_of_brewing_company(user, brewing_company):
    """Checks the user is a member of the brewing_company group.

    Args:
        user: The django user to check membership for.
        brewing_company: The BrewingCompany to check membership in its
            associated group.
    """
    if brewing_company.group is None:
        return False

    return user in brewing_company.group.user_set.all()
