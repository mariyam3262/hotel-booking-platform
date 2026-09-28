from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Booking


from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Property, Membership


@receiver(post_save, sender=Property)
def grant_creator_membership(sender, instance, created, **kwargs):
    if created and hasattr(instance, "_created_by") and instance._created_by:
        Membership.objects.get_or_create(
            property=instance,
            user=instance._created_by,
            defaults={"role": "owner"},
        )

@receiver([post_save, post_delete], sender=Booking)
def invalidate_availability_cache(sender, **kwargs):
    # simplest correct approach: clear all availability cache entries.
    # A more surgical version would only clear keys for the affected room_type,
    # but that requires tracking which cache keys map to which room_type —
    # not worth the complexity for a 60-second TTL.
    cache.delete_pattern("availability:*")

from django.db.models.signals import post_save
from .models import Property


@receiver(post_save, sender=Property)
def trigger_ai_description(sender, instance, created, **kwargs):
    if created and not instance.ai_description:
        from hotels.ai_tasks import generate_property_description
        generate_property_description.delay(instance.id)


from .models import Review

@receiver(post_save, sender=Review)
def trigger_review_embedding(sender, instance, created, **kwargs):
    if created:
        from hotels.ai_tasks import generate_review_embedding
        generate_review_embedding.delay(instance.id)