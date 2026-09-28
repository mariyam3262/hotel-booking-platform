import hashlib
import json

from django.core.cache import cache
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from pgvector.django import CosineDistance
from google import genai
from google.genai import types

from .models import Property, Room, Booking, Guest, RoomType, Membership, Review
from .forms import BookingForm, GuestForm
from .serializers import PropertySerializer, BookingSerializer, RoomSerializer, MembershipSerializer,  RoomTypeWriteSerializer, RoomWriteSerializer
from .permissions import IsPropertyMember
from .throttles import AIEndpointThrottle
from .services import build_concierge_context


# ---- Function-based views (Days 1-3) — kept for reference, superseded by Vue + API in Phase 7 ----

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


# ---- DRF ViewSets ----

class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated, IsPropertyMember]

    def get_queryset(self):
        member_property_ids = Membership.objects.filter(user=self.request.user).values_list("property_id", flat=True)
        return Property.objects.filter(id__in=member_property_ids).prefetch_related("room_types__rooms")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, organization=self._get_or_create_org())

    def _get_or_create_org(self):
        # for now, every user's properties belong to one org named after them —
        # a real multi-org product would let the user pick/create this explicitly
        from .models import Organization
        org, _ = Organization.objects.get_or_create(
            name=f"{self.request.user.username}'s Organization",
            slug=f"org-{self.request.user.id}",
        )
        return org

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsPropertyMember]

    def get_queryset(self):
        member_property_ids = Membership.objects.filter(user=self.request.user).values_list("property_id", flat=True)
        return Booking.objects.filter(
            room__room_type__property_id__in=member_property_ids
        ).select_related("room__room_type__property", "guest")


class RoomTypeViewSet(viewsets.ModelViewSet):
    serializer_class = RoomTypeWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        member_property_ids = Membership.objects.filter(user=self.request.user).values_list("property_id", flat=True)
        return RoomType.objects.filter(property_id__in=member_property_ids)

    def perform_create(self, serializer):
        property_obj = serializer.validated_data["property"]
        is_member = Membership.objects.filter(property=property_obj, user=self.request.user).exists()
        if not is_member:
            raise serializers.ValidationError("You do not have access to this property.")
        serializer.save()


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        member_property_ids = Membership.objects.filter(user=self.request.user).values_list("property_id", flat=True)
        return Room.objects.filter(room_type__property_id__in=member_property_ids)

    def perform_create(self, serializer):
        room_type = serializer.validated_data["room_type"]
        is_member = Membership.objects.filter(property=room_type.property, user=self.request.user).exists()
        if not is_member:
            raise serializers.ValidationError("You do not have access to this property.")
        serializer.save()


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


# ---- AI: semantic review search ----

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([AIEndpointThrottle])
def semantic_review_search(request):
    query = request.data.get("query")
    property_id = request.data.get("property_id")

    if not query or not property_id:
        return Response({"error": "query and property_id are required"}, status=400)

    property_obj = get_object_or_404(Property, pk=property_id)
    is_member = Membership.objects.filter(property=property_obj, user=request.user).exists()
    if not is_member:
        return Response({"error": "You do not have access to this property."}, status=403)

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    result = client.models.embed_content(model="gemini-embedding-001", contents=query)
    query_embedding = result.embeddings[0].values

    reviews = (
        Review.objects.filter(property=property_obj, embedding__isnull=False)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:10]
    )

    data = [
        {"id": r.id, "rating": r.rating, "body": r.body, "distance": r.distance}
        for r in reviews
    ]
    return Response(data)


# ---- AI: RAG concierge (non-streaming, cached) ----

def _concierge_cache_key(property_id, question):
    normalized = question.strip().lower()
    raw = f"{property_id}:{normalized}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"concierge:{digest}"


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([AIEndpointThrottle])
def ask_concierge(request):
    question = request.data.get("question")
    property_id = request.data.get("property_id")

    if not question or not property_id:
        return Response({"error": "question and property_id are required"}, status=400)

    property_obj = get_object_or_404(Property, pk=property_id)
    is_member = Membership.objects.filter(property=property_obj, user=request.user).exists()
    if not is_member:
        return Response({"error": "You do not have access to this property."}, status=403)

    cache_key = _concierge_cache_key(property_id, question)
    cached = cache.get(cache_key)
    if cached:
        return Response({**cached, "cached": True})

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    context_block, sources = build_concierge_context(client, property_obj, question)

    prompt = (
        "You are a helpful hotel concierge. Answer the guest's question using "
        "ONLY the information below. If the information doesn't answer the "
        "question, say so honestly and suggest they contact the front desk "
        "directly, rather than guessing.\n\n"
        f"--- PROPERTY INFORMATION ---\n{context_block}\n--- END ---\n\n"
        f"Guest question: {question}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                http_options=types.HttpOptions(timeout=10_000),
            ),
        )
    except Exception:
        return Response(
            {"answer": "The concierge service is temporarily unavailable. Please try again shortly.", "error": True},
            status=503,
        )

    result = {"answer": response.text, "sources": sources}
    cache.set(cache_key, result, timeout=600)
    return Response(result)


# ---- AI: RAG concierge (streaming, SSE) ----

from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

def _authenticate(request):
    auth = JWTAuthentication()
    try:
        result = auth.authenticate(request)
    except (InvalidToken, AuthenticationFailed):
        return None
    if result is None:
        return None
    user, _ = result
    return user


@csrf_exempt
@require_POST
def ask_concierge_stream(request):
    user = _authenticate(request)
    if user is None:
        return JsonResponse({"error": "Authentication required"}, status=401)

    body = json.loads(request.body)
    question = body.get("question")
    property_id = body.get("property_id")

    if not question or not property_id:
        return JsonResponse({"error": "question and property_id are required"}, status=400)

    property_obj = get_object_or_404(Property, pk=property_id)
    is_member = Membership.objects.filter(property=property_obj, user=user).exists()
    if not is_member:
        return JsonResponse({"error": "You do not have access to this property."}, status=403)

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    context_block, sources = build_concierge_context(client, property_obj, question)

    def event_stream():
        yield f"data: {json.dumps({'type': 'sources', **sources})}\n\n"

        prompt = (
            "You are a helpful hotel concierge. Answer using ONLY the "
            "information below. If unclear, say so honestly rather than "
            "guessing.\n\n"
            f"--- PROPERTY INFORMATION ---\n{context_block}\n--- END ---\n\n"
            f"Guest question: {question}"
        )

        stream = client.models.generate_content_stream(model="gemini-3.6-flash", contents=prompt)
        for chunk in stream:
            if chunk.text:
                yield f"data: {json.dumps({'type': 'answer_chunk', 'text': chunk.text})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response

class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        member_property_ids = Membership.objects.filter(user=self.request.user).values_list('property_id', flat=True)
        return Membership.objects.filter(property_id__in=member_property_ids).select_related('user')

    def perform_create(self, serializer):
        property_obj = serializer.validated_data['property']
        is_member = Membership.objects.filter(property=property_obj, user=self.request.user).exists()
        if not is_member:
            raise serializers.ValidationError('You do not have access to this property.')
        serializer.save()
