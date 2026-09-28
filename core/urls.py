"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hotels import views
from hotels.views import PropertyViewSet, BookingViewSet, semantic_review_search
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


router = DefaultRouter()
router.register("api/v1/properties", PropertyViewSet, basename="property")
router.register("api/v1/bookings", BookingViewSet, basename="booking")
router.register("api/v1/room-types", views.RoomTypeViewSet, basename="roomtype")
router.register("api/v1/rooms", views.RoomViewSet, basename="room")
router.register("api/v1/memberships", views.MembershipViewSet, basename="membership")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hotels/', include('hotels.urls')),
    path("", include(router.urls)),

    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),    
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("api/v1/reviews/search/", semantic_review_search, name="semantic_review_search"),
    path("api/v1/availability", views.check_availability, name="check_availability"),
    path("api/v1/concierge/ask/", views.ask_concierge, name="ask_concierge"),
    path("api/v1/concierge/ask/stream/", views.ask_concierge_stream, name="ask_concierge_stream"),
]
