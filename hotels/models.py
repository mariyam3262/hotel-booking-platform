from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import DateRangeField
from psycopg2.extras import DateRange

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db.models import Q


class Organization(models.Model):
    """A hotel chain — the top-level tenant."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Property(models.Model):
    """A single hotel belonging to an Organization."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="properties")
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.city})"


class Membership(models.Model):
    """Staff access — scoped to a Property, not the whole Organization."""
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("manager", "Manager"),
        ("front_desk", "Front Desk"),
    ]
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="front_desk")

    class Meta:
        unique_together = ("property", "user")

    def __str__(self):
        return f"{self.user} @ {self.property} ({self.role})"


class RoomType(models.Model):
    """e.g. Deluxe, Suite — a category of room within a Property."""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="room_types")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    max_occupancy = models.PositiveIntegerField(default=2)

    def __str__(self):
        return f"{self.name} @ {self.property}"


class Room(models.Model):
    """A physical room — this is what actually gets booked."""
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=20)
    floor = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)  # for taking a room out of service

    class Meta:
        unique_together = ("room_type", "room_number")

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name})"

    def is_available(self, check_in, check_out, exclude_booking_id=None):
        overlapping = self.bookings.filter(
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exclude(status="cancelled")

        if exclude_booking_id:
            overlapping = overlapping.exclude(pk=exclude_booking_id)

        return not overlapping.exists()


class Guest(models.Model):
    """The person staying — not a User account, just contact info."""
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("checked_in", "Checked In"),
        ("checked_out", "Checked Out"),
        ("cancelled", "Cancelled"),
    ]
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="bookings_created")
    created_at = models.DateTimeField(auto_now_add=True)
    stay_range = DateRangeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        # '[)' = inclusive start, exclusive end — matches your check_in__lt/check_out__gt
        # logic from Day 3, so Case D (adjacent bookings) still correctly doesn't conflict
        self.stay_range = DateRange(self.check_in, self.check_out, bounds="[)")
        super().save(*args, **kwargs)
    

    def __str__(self):
        return f"{self.guest} — {self.room} ({self.check_in} to {self.check_out})"

    class Meta:
        constraints = [
            ExclusionConstraint(
                name="exclude_overlapping_bookings",
                expressions=[
                    ("room", RangeOperators.EQUAL),
                    ("stay_range", RangeOperators.OVERLAPS),
                ],
                condition=Q(status__in=["pending", "confirmed", "checked_in"]),
            ),
        ]
        indexes = [
            models.Index(fields=["room", "check_in", "check_out"]),
            models.Index(fields=["status"]),
        ]


class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, default="card")
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.amount} for {self.booking}"


class Review(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="reviews")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="reviews")
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, related_name="review")
    rating = models.PositiveSmallIntegerField()  # 1-5
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating}★ — {self.property} by {self.guest}"

class FailedTaskLog(models.Model):
    task_name = models.CharField(max_length=255)
    task_args = models.TextField()
    error_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task_name} failed at {self.created_at}"


class AuditLog(models.Model):
    ACTION_CHOICES = [("create", "Create"), ("update", "Update"), ("delete", "Delete")]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)
    changes = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name}#{self.object_id}"