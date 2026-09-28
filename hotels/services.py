from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db import transaction, IntegrityError
from .models import Booking, Room, Guest


@transaction.atomic
def create_booking_safely(room_id, guest_data, check_in, check_out, total_price, created_by, idempotency_key=None):
    if idempotency_key:
        existing = Booking.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing  # already created — return it, don't book again

    room = Room.objects.select_for_update().get(id=room_id)

    conflicts = Booking.objects.filter(
        room=room, check_in__lt=check_out, check_out__gt=check_in,
    ).exclude(status="cancelled")
    if conflicts.exists():
        raise ValueError(f"Room {room.room_number} is already booked for part of this range.")

    guest, _ = Guest.objects.get_or_create(email=guest_data["email"], defaults=guest_data)

    try:
        booking = Booking.objects.create(
            room=room, guest=guest, check_in=check_in, check_out=check_out,
            total_price=total_price, created_by=created_by, idempotency_key=idempotency_key,
        )
    except IntegrityError:
        raise ValueError(f"Room {room.room_number} is already booked for part of this range.")

    from hotels.tasks import send_booking_confirmation_email, send_checkin_reminder
    from datetime import datetime, timedelta, time
    from django.utils import timezone

    send_booking_confirmation_email.delay(booking.id)

    reminder_time = timezone.make_aware(datetime.combine(check_in - timedelta(days=1), time(9, 0)))
    if reminder_time > timezone.now():
        send_checkin_reminder.apply_async(args=[booking.id], eta=reminder_time)

    return booking


from pgvector.django import CosineDistance
from .models import RoomType, Review


def build_concierge_context(client, property_obj, question):
    room_types = RoomType.objects.filter(property=property_obj)
    room_info = "\n".join(
        f"- {rt.name}: {rt.description or 'No description'} "
        f"(${rt.base_price_per_night}/night, sleeps {rt.max_occupancy})"
        for rt in room_types
    )

    embed_result = client.models.embed_content(model="gemini-embedding-001", contents=question)
    question_embedding = embed_result.embeddings[0].values

    relevant_reviews = list(
        Review.objects.filter(property=property_obj, embedding__isnull=False)
        .annotate(distance=CosineDistance("embedding", question_embedding))
        .filter(distance__lt=0.7)
        .order_by("distance")[:3]
    )
    review_info = "\n".join(f"- \"{r.body}\" ({r.rating}/5 stars)" for r in relevant_reviews)

    context_block = (
        f"Property: {property_obj.name}\n"
        f"Location: {property_obj.city}, {property_obj.country}\n"
        f"About: {property_obj.ai_description or 'No description available'}\n\n"
        f"Room Types:\n{room_info or 'No room type info available'}\n\n"
        f"Relevant Guest Reviews:\n{review_info or 'No relevant reviews found'}"
    )

    sources = {
        "room_types_used": room_types.count(),
        "reviews_used": [{"id": r.id, "rating": r.rating} for r in relevant_reviews],
    }

    return context_block, sources