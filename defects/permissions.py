from rest_framework import permissions

class IsProductOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Product Owner').exists()

class IsDeveloper(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Developer').exists()

class IsTester(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Tester').exists()

from rest_framework import permissions

class IsProductOwnerOrDeveloperForDefect(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['Product Owner', 'Developer']).exists()
    def has_object_permission(self, request, view, obj):
        product = obj.product
        if request.user == product.owner:
            return True
        if request.user in product.developers.all():
            return True
        return False