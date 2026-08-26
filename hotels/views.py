import hashlib

from django.core.cache import cache
from django.shortcuts import render, get_object_or_404, redirect

from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Property, Room, Booking, Guest, RoomType
from .forms import BookingForm, GuestForm
from .serializers import PropertySerializer, BookingSerializer, RoomSerializer


# ---- Function-based views (Days 1-3) ----

def property_list(request):
    properties = Property.objects.all()
    return render(request, "hotels/property_list.html", {"properties": properties})


def property_detail(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    rooms = Room.objects.filter(room_type__property=property_obj)
    return render(request, "hotels/property_detail.html", {"property": property_obj, "rooms": rooms})


def booking_create(request):
    if request.method == "POST":
        guest_form = GuestForm(request.POST)
        booking_form = BookingForm(request.POST)
        if guest_form.is_valid() and booking_form.is_valid():
            guest = guest_form.save()
            booking = booking_form.save(commit=False)
            booking.guest = guest
            booking.created_by = request.user
            booking.save()
            return redirect("booking_detail", pk=booking.pk)
    else:
        guest_form = GuestForm()
        booking_form = BookingForm()
    return render(request, "hotels/booking_form.html", {
        "guest_form": guest_form,
        "booking_form": booking_form,
    })


def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    return render(request, "hotels/booking_detail.html", {"booking": booking})


def booking_update(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect("booking_detail", pk=booking.pk)
    else:
        form = BookingForm(instance=booking)
    return render(request, "hotels/booking_form.html", {"booking_form": form})


def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        booking.status = "cancelled"
        booking.save(update_fields=["status"])
        return redirect("property_list")
    return render(request, "hotels/booking_confirm_cancel.html", {"booking": booking})


from .permissions import IsPropertyMember
from .models import Membership

class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated, IsPropertyMember]

    def get_queryset(self):
        # list should only show properties the user is actually a member of
        member_property_ids = Membership.objects.filter(user=self.request.user).values_list("property_id", flat=True)
        return Property.objects.filter(id__in=member_property_ids).prefetch_related("room_types__rooms")


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsPropertyMember]

    def get_queryset(self):
        member_property_ids = Membership.objects.filter(user=self.request.user).values_list("property_id", flat=True)
        return Booking.objects.filter(
            room__room_type__property_id__in=member_property_ids
        ).select_related("room__room_type__property", "guest")


# ---- Availability search (cached) ----

def _availability_cache_key(room_type_id, check_in, check_out):
    raw = f"{room_type_id}:{check_in}:{check_out}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"availability:{digest}"


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def check_availability(request):
    room_type_id = request.query_params.get("room_type")
    check_in = request.query_params.get("check_in")
    check_out = request.query_params.get("check_out")

    if not all([room_type_id, check_in, check_out]):
        return Response({"error": "room_type, check_in, and check_out are required"}, status=400)

    room_type = get_object_or_404(RoomType, pk=room_type_id)
    is_member = Membership.objects.filter(property=room_type.property, user=request.user).exists()
    if not is_member:
        return Response({"error": "You do not have access to this property."}, status=403)

    cache_key = _availability_cache_key(room_type_id, check_in, check_out)
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    conflicting_room_ids = Booking.objects.filter(
        room__room_type_id=room_type_id,
        check_in__lt=check_out,
        check_out__gt=check_in,
    ).exclude(status="cancelled").values_list("room_id", flat=True)

    available_rooms = Room.objects.filter(
        room_type_id=room_type_id, is_active=True
    ).exclude(id__in=conflicting_room_ids)

    data = RoomSerializer(available_rooms, many=True).data
    cache.set(cache_key, data, timeout=60)
    return Response(data)