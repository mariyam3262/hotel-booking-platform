from celery import shared_task, Task as CeleryTask
from celery.utils.log import get_task_logger
from django.core.mail import send_mail

logger = get_task_logger(__name__)


class DeadLetterTask(CeleryTask):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from hotels.models import FailedTaskLog
        FailedTaskLog.objects.create(
            task_name=self.name,
            task_args=str(args),
            error_message=str(exc),
        )
        logger.error(f"Task {self.name} permanently failed after retries: {exc}")


@shared_task(bind=True, base=DeadLetterTask, max_retries=3)
def send_booking_confirmation_email(self, booking_id):
    from hotels.models import Booking
    try:
        booking = Booking.objects.select_related("guest", "room__room_type__property").get(id=booking_id)
    except Booking.DoesNotExist:
        return  # nothing to send, don't retry

    try:
        property_name = booking.room.room_type.property.name
        send_mail(
            subject=f"Booking Confirmed — {property_name}",
            message=(
                f"Hi {booking.guest.full_name},\n\n"
                f"Your booking at {property_name} is confirmed.\n"
                f"Room: {booking.room.room_number}\n"
                f"Check-in: {booking.check_in}\n"
                f"Check-out: {booking.check_out}\n"
                f"Total: {booking.total_price}\n\n"
                f"See you soon!"
            ),
            from_email="noreply@example.com",
            recipient_list=[booking.guest.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, base=DeadLetterTask, max_retries=3)
def send_checkin_reminder(self, booking_id):
    from hotels.models import Booking
    try:
        booking = Booking.objects.select_related("guest", "room__room_type__property").get(id=booking_id)
    except Booking.DoesNotExist:
        return

    if booking.status not in ("pending", "confirmed"):
        return

    try:
        send_mail(
            subject=f"Your stay at {booking.room.room_type.property.name} is coming up",
            message=f"Hi {booking.guest.full_name}, reminder — your check-in is on {booking.check_in}.",
            from_email="noreply@example.com",
            recipient_list=[booking.guest.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, base=DeadLetterTask)
def cancel_unpaid_bookings(self):
    from hotels.models import Booking
    from django.utils import timezone
    from datetime import timedelta

    grace_period = timezone.now() - timedelta(hours=24)
    stale_bookings = Booking.objects.filter(status="pending", created_at__lt=grace_period)
    count = stale_bookings.update(status="cancelled")
    logger.info(f"Auto-cancelled {count} unpaid bookings past the grace period.")
    return count