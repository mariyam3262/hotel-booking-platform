from django.contrib import admin
from .models import Organization, Property, Membership, RoomType, Room, Guest, Booking, Payment, Review

admin.site.register(Organization)
admin.site.register(Property)
admin.site.register(Membership)
admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(Guest)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Review)