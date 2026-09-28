from django.contrib import admin
from .models import Organization, Property, Membership, RoomType, Room, Guest, Booking, Payment, Review

from .models import Property

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not change:  # only on creation, not edits
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Organization)
admin.site.register(Membership)
admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(Guest)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Review)