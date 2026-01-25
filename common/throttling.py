from rest_framework.throttling import AnonRateThrottle


class IPThrottle(AnonRateThrottle):
    """
    IP-based throttle PER ENDPOINT.
    Prevents one IP from spamming many different email/username combos on same endpoint.
    """
    scope = 'ip_throttle'
    
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        view_name = view.__class__.__name__
        return self.cache_format % {
            'scope': self.scope,
            'ident': f"{view_name}:{ident}"
        }


class AuthThrottle(AnonRateThrottle):
    """
    Credential-based throttle PER ENDPOINT.
    Identifies by IP + identifier (email/username) + endpoint.
    """
    scope = 'auth_throttle'

    def get_cache_key(self, request, view):
        ident_name = request.data.get('username') or request.data.get('email', '').strip().lower()
        if not ident_name:
            return super().get_cache_key(request, view)

        ident = self.get_ident(request)
        view_name = view.__class__.__name__
        return self.cache_format % {
            'scope': self.scope,
            'ident': f"{view_name}:{ident}:{ident_name}"
        }

