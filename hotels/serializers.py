from rest_framework import serializers
from django.db import IntegrityError
from .models import Organization, Property, AuditLog, RoomType, Room, Guest, Booking, Payment, Review, Membership
from .services import create_booking_safely


class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = ["id", "full_name", "email", "phone"]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "room_number", "floor", "is_active"]

class RoomDetailSerializer(serializers.ModelSerializer):
    """Nested, read-only room representation for booking display."""
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)

    class Meta:
        model = Room
        fields = ["id", "room_number", "room_type_name"]


class RoomTypeSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)

    class Meta:
        model = RoomType
        fields = ["id", "name", "description", "base_price_per_night", "max_occupancy", "rooms"]


class PropertySerializer(serializers.ModelSerializer):
    room_types = RoomTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = ["id", "name", "address", "city", "country", "room_types"]


class BookingSerializer(serializers.ModelSerializer):
    guest = GuestSerializer()
    room_detail = RoomDetailSerializer(source="room", read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "room", "room_detail", "guest", "check_in", "check_out", "status", "total_price", "created_at"]
        read_only_fields = ["status", "created_at"]

    def validate(self, data):
        request = self.context["request"]
        room = data.get("room")
        check_in = data.get("check_in")
        check_out = data.get("check_out")

        # 1. membership check — does this user work at this room's property?
        property_obj = room.room_type.property
        is_member = Membership.objects.filter(property=property_obj, user=request.user).exists()
        if not is_member:
            raise serializers.ValidationError("You do not have access to create bookings at this property.")

        # 2. date sanity check
        if check_out <= check_in:
            raise serializers.ValidationError("Check-out date must be after check-in date.")

        # 3. application-level overlap check (fast-path UX; DB constraint is the real safety net)
        conflicts = Booking.objects.filter(
            room=room,
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exclude(status="cancelled")

        if self.instance:
            conflicts = conflicts.exclude(pk=self.instance.pk)

        if conflicts.exists():
            raise serializers.ValidationError(f"Room {room.room_number} is already booked for part of this range.")

        return data

    def create(self, validated_data):
        guest_data = validated_data.pop("guest")
        request = self.context["request"]
        idempotency_key = request.headers.get("Idempotency-Key")

        try:
            booking = create_booking_safely(
                room_id=validated_data["room"].id,
                guest_data=guest_data,
                check_in=validated_data["check_in"],
                check_out=validated_data["check_out"],
                total_price=validated_data["total_price"],
                created_by=request.user,
                idempotency_key=idempotency_key,
            )
        except (ValueError, IntegrityError):
            raise serializers.ValidationError("This room is already booked for part of the selected date range.")
        return booking

    from .models import AuditLog

    def update(self, instance, validated_data):
        request = self.context["request"]
        changes = {}
        for field in ["status", "check_in", "check_out", "total_price"]:
            if field in validated_data:
                old_value = getattr(instance, field)
                new_value = validated_data[field]
                if old_value != new_value:
                    changes[field] = {"old": str(old_value), "new": str(new_value)}

        instance = super().update(instance, validated_data)

        if changes:
            AuditLog.objects.create(
                user=request.user,
                action="update",
                model_name="Booking",
                object_id=str(instance.id),
                changes=changes,
            )
        return instance

class RoomTypeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ["id", "property", "name", "description", "base_price_per_night", "max_occupancy"]


class RoomWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "room_type", "room_number", "floor", "is_active"]


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_username = serializers.CharField(write_only=True)

    class Meta:
        model = Membership
        fields = ["id", "property", "user_username", "username", "role"]

    def create(self, validated_data):
        username = validated_data.pop("user_username")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"No user found with username '{username}'.")
        return Membership.objects.create(user=user, **validated_data)