from rest_framework import permissions
from .models import Membership


class IsPropertyMember(permissions.BasePermission):
    """
    Grants access only if the requesting user has a Membership
    at the Property the object belongs to.
    """

    def has_object_permission(self, request, view, obj):
        property_obj = self._resolve_property(obj)
        if property_obj is None:
            return False
        return Membership.objects.filter(property=property_obj, user=request.user).exists()

    def _resolve_property(self, obj):
        # obj might BE a Property, or something nested under one —
        # walk up the relationship chain depending on what we're given.
        if hasattr(obj, "room_types"):          # obj is a Property
            return obj
        if hasattr(obj, "property"):            # obj is a RoomType
            return obj.property
        if hasattr(obj, "room_type"):           # obj is a Room
            return obj.room_type.property
        if hasattr(obj, "room"):                # obj is a Booking
            return obj.room.room_type.property
        return None