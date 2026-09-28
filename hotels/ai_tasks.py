from celery import shared_task
from django.conf import settings
from google import genai

from hotels.tasks import DeadLetterTask, logger


@shared_task(bind=True, base=DeadLetterTask, max_retries=3)
def generate_property_description(self, property_id):
    from hotels.models import Property

    try:
        prop = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=(
                f"Write a warm, inviting 2-3 sentence description for a hotel "
                f"listing. The property is called '{prop.name}', located in "
                f"{prop.city}, {prop.country}. Return only the description, "
                f"no preamble."
            ),
        )
        prop.ai_description = response.text.strip()
        prop.save(update_fields=["ai_description"])

    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task(bind=True, base=DeadLetterTask, max_retries=3)
def generate_review_embedding(self, review_id):
    from hotels.models import Review

    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=review.body,
        )
        review.embedding = result.embeddings[0].values
        review.save(update_fields=["embedding"])

    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)