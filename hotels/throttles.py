from rest_framework.throttling import UserRateThrottle


class AIEndpointThrottle(UserRateThrottle):
    scope = "ai_endpoint"