from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Booking


@receiver([post_save, post_delete], sender=Booking)
def invalidate_availability_cache(sender, **kwargs):
    # simplest correct approach: clear all availability cache entries.
    # A more surgical version would only clear keys for the affected room_type,
    # but that requires tracking which cache keys map to which room_type —
    # not worth the complexity for a 60-second TTL.
    cache.delete_pattern("availability:*")