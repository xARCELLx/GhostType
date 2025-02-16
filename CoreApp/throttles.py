from rest_framework.throttling import ScopedRateThrottle

class SubscriptionThrottle(ScopedRateThrottle):
    scope = 'subscription'  

    def allow_request(self, request, view):
        user = request.user
        if user.is_authenticated and hasattr(user, 'subscription_status') and user.subscription_status:
            return True  
        
        return super().allow_request(request, view)
