from rest_framework import permissions


class IsPropertyLandlord(permissions.BasePermission):
    """
    Allows access only to the landlord who owns the property
    tied to this application.
    """
    def has_object_permission(self, request, view, obj):
        return obj.property.landlord_id == request.user.id