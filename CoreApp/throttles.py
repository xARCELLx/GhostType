from rest_framework.throttling import UserRateThrottle

class SubscriptionThrottle(UserRateThrottle):
    scope = "non_subscribed"
    def get_rate(self):
        rate = super().get_rate()
        print(f"Throttle rate for scope '{self.scope}': {rate}")  # Debugging line
        return rate
    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)
        print(f"Throttle applied: {not allowed}, User: {request.user}, Scope: {self.scope}")
        return allowed


    